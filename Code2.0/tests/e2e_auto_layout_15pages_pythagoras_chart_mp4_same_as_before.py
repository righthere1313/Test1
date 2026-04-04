import os
import time
from pathlib import Path

import httpx


def _require_env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise SystemExit(f"Missing env: {name}")
    return v


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    out_dir = base_dir / "tests" / "e2e_outputs" / f"auto_layout_mp4_pages_{int(time.time())}"
    out_dir.mkdir(parents=True, exist_ok=True)
    pages_out_dir = out_dir / "mp4_pages"
    pages_out_dir.mkdir(parents=True, exist_ok=True)

    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    layout = os.getenv("LAYOUT", "general")
    slides_total = int(os.getenv("SLIDES_TOTAL", "15"))
    poll_timeout_s = int(os.getenv("POLL_TIMEOUT_SECONDS", "10800"))
    poll_interval_s = float(os.getenv("POLL_INTERVAL_SECONDS", "5"))
    mp4_portrait = os.getenv("MP4_PORTRAIT", "").strip() or None
    mp4_max_wait_seconds = int(os.getenv("MP4_MAX_WAIT_SECONDS", "1800"))

    _require_env("DASHSCOPE_API_KEY")
    _require_env("OSS_ACCESS_KEY_ID")
    _require_env("OSS_ACCESS_KEY_SECRET")
    _require_env("OSS_BUCKET_NAME")
    _require_env("OSS_ENDPOINT")

    source_text = os.getenv(
        "SOURCE_TEXT",
        "请生成一份关于数学“勾股定理”的15页课件，包含定义、证明思路、三个例题、常见误区、练习题与总结。",
    )

    extra_instructions = (
        "必须至少包含一张图表。请在第2页（slides[1]）加入 chart 字段，严格按如下结构输出：\n"
        '{ "id":"bar_chart", "title":"例题类型分布", "subtitle":"勾股定理常见题型", "position":"right", "policy":"trim", '
        '"data": { "categories": ["直角三角形", "距离计算", "坐标几何", "实际应用", "综合题"], "values": [5, 3, 2, 4, 1] } }\n'
        "除该字段外其它字段按原有规则输出。"
    )

    payload = {
        "layout": layout,
        "source_text": source_text,
        "slides_total": slides_total,
        "title": "勾股定理",
        "subtitle": "15页端到端测试",
        "extra_instructions": extra_instructions,
        "with_mp4": True,
        "mp4_portrait": mp4_portrait,
        "mp4_max_wait_seconds": mp4_max_wait_seconds,
    }

    with httpx.Client(timeout=180) as client:
        r = client.post(f"{base_url}/api/v1/generate/ppt/auto_layout", json=payload)
        if r.status_code != 200:
            raise SystemExit(f"auto_layout failed: {r.status_code} {r.text}")
        resp = r.json()

        ppt_filename = resp.get("filename")
        ppt_url = resp.get("download_url")
        job_id = resp.get("mp4_job_id")
        mp4_status_url = resp.get("mp4_status_url")
        mp4_pages_base_url = resp.get("mp4_pages_base_url")
        mp4_total_pages = int(resp.get("mp4_total_pages") or 0)
        if not ppt_filename or not ppt_url:
            raise SystemExit(f"missing ppt fields: {resp}")
        if not job_id or not mp4_status_url or not mp4_pages_base_url or mp4_total_pages <= 0:
            raise SystemExit(f"missing mp4 fields: {resp}")

        print("[+] pptx:", ppt_filename)
        print("[+] mp4 job:", job_id)
        print("[+] out dir:", out_dir)

        ppt_path = out_dir / ppt_filename
        with client.stream("GET", f"{base_url}{ppt_url}") as dr:
            if dr.status_code != 200:
                raise SystemExit(f"download ppt failed: {dr.status_code} {dr.text}")
            with open(ppt_path, "wb") as f:
                for chunk in dr.iter_bytes(1024 * 256):
                    if chunk:
                        f.write(chunk)

        deadline = time.time() + poll_timeout_s
        saved = set()
        last_status = None

        while time.time() < deadline:
            rr = client.get(f"{base_url}{mp4_status_url}", timeout=30)
            if rr.status_code != 200:
                raise SystemExit(f"poll mp4 failed: {rr.status_code} {rr.text}")
            meta = rr.json()
            status = meta.get("status")
            prog = meta.get("progress") or {}
            if status != last_status:
                print(f"[*] mp4 status={status}")
                last_status = status
            print(f"    progress: {prog.get('done_pages')}/{prog.get('total_pages')}")

            pages = meta.get("pages") if isinstance(meta.get("pages"), dict) else {}
            for i in range(1, mp4_total_pages + 1):
                if i in saved:
                    continue
                st = pages.get(str(i)) if isinstance(pages.get(str(i)), dict) else {}
                if st.get("status") != "done":
                    continue
                url = f"{base_url}{mp4_pages_base_url}/{i}.mp4"
                out_path = pages_out_dir / f"page_{i}.mp4"
                with client.stream("GET", url, timeout=600) as vr:
                    if vr.status_code != 200:
                        continue
                    with open(out_path, "wb") as f:
                        for chunk in vr.iter_bytes(1024 * 256):
                            if chunk:
                                f.write(chunk)
                if out_path.exists() and out_path.stat().st_size > 0:
                    saved.add(i)

            if len(saved) >= mp4_total_pages and status in {"done", "failed"}:
                break
            if status == "done" and len(saved) >= mp4_total_pages:
                break
            time.sleep(poll_interval_s)

        print("[+] saved pptx:", ppt_path)
        print("[+] saved mp4 pages:", len(saved), "/", mp4_total_pages)
        print("[+] mp4 pages dir:", pages_out_dir)


if __name__ == "__main__":
    main()


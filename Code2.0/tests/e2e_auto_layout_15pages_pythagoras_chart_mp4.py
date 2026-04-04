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
    out_dir = base_dir / "tests" / "e2e_outputs" / f"auto_layout_mp4_{int(time.time())}"
    out_dir.mkdir(parents=True, exist_ok=True)

    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    layout = os.getenv("LAYOUT", "general")

    _require_env("DASHSCOPE_API_KEY")
    _require_env("OSS_ACCESS_KEY_ID")
    _require_env("OSS_ACCESS_KEY_SECRET")
    _require_env("OSS_BUCKET_NAME")
    _require_env("OSS_ENDPOINT")

    slides_total = int(os.getenv("SLIDES_TOTAL", "15"))
    poll_timeout_s = int(os.getenv("POLL_TIMEOUT_SECONDS", "5400"))
    poll_interval_s = float(os.getenv("POLL_INTERVAL_SECONDS", "5"))
    mp4_portrait = os.getenv("MP4_PORTRAIT", "").strip() or None

    source_text = os.getenv(
        "SOURCE_TEXT",
        "请生成一份关于数学“勾股定理”的15页课件，包含定义、证明思路、三个例题、常见误区、练习题与总结。",
    )

    extra_instructions = (
        "请在第2页（slides[1]）加入一个柱状图字段 chart，严格按如下结构输出：\n"
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
    }

    with httpx.Client(timeout=120) as client:
        r = client.post(f"{base_url}/api/v1/generate/ppt/auto_layout", json=payload)
        r.raise_for_status()
        resp = r.json()

        ppt_filename = resp.get("filename")
        ppt_url = resp.get("download_url")
        job_id = resp.get("mp4_job_id")
        mp4_status_url = resp.get("mp4_status_url")
        mp4_url = resp.get("mp4_download_url")
        if not all([ppt_filename, ppt_url, job_id, mp4_status_url, mp4_url]):
            raise SystemExit(f"missing fields in response: {resp}")

        print("[+] pptx:", ppt_filename)
        print("[+] pptx url:", ppt_url)
        print("[+] mp4 job:", job_id)
        print("[+] mp4 status url:", mp4_status_url)
        print("[+] mp4 url:", mp4_url)

        ppt_path = out_dir / ppt_filename
        with client.stream("GET", f"{base_url}{ppt_url}") as dr:
            dr.raise_for_status()
            with open(ppt_path, "wb") as f:
                for chunk in dr.iter_bytes(1024 * 256):
                    if not chunk:
                        continue
                    f.write(chunk)
        print("[+] saved pptx:", ppt_path)

        deadline = time.time() + poll_timeout_s
        last_status = None
        while time.time() < deadline:
            rr = client.get(f"{base_url}{mp4_status_url}")
            rr.raise_for_status()
            meta = rr.json()
            status = meta.get("status")
            prog = meta.get("progress") or {}
            if status != last_status:
                print(f"[*] mp4 status={status}")
                last_status = status
            print(f"    progress: {prog.get('done_pages')}/{prog.get('total_pages')}")
            if status == "done":
                break
            if status == "failed":
                raise SystemExit(f"mp4 failed: {meta.get('error')}")
            time.sleep(poll_interval_s)

        mp4_path = out_dir / f"{job_id}.mp4"
        with client.stream("GET", f"{base_url}{mp4_url}") as vr:
            vr.raise_for_status()
            with open(mp4_path, "wb") as f:
                for chunk in vr.iter_bytes(1024 * 256):
                    if not chunk:
                        continue
                    f.write(chunk)
        print("[+] saved mp4:", mp4_path)


if __name__ == "__main__":
    main()


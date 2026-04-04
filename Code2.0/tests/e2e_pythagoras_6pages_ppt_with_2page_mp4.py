import os
import sys
import time
from pathlib import Path

import httpx


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(base_dir))
    out_dir = base_dir / "tests" / "e2e_outputs" / f"pythagoras_6p_mp4_2p_{int(time.time())}"
    out_dir.mkdir(parents=True, exist_ok=True)

    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    poll_timeout_s = int(os.getenv("POLL_TIMEOUT_SECONDS", "10800"))
    poll_interval_s = float(os.getenv("POLL_INTERVAL_SECONDS", "5"))
    mp4_portrait = os.getenv("MP4_PORTRAIT", "").strip() or None
    mp4_max_wait_seconds = int(os.getenv("MP4_MAX_WAIT_SECONDS", "1800"))

    plan = {
        "title": "勾股定理",
        "subtitle": "6页测试（前2页数字人）",
        "template": None,
        "layout": "general",
        "cover_blocks": [["勾股定理"], ["定义、公式、例题"], ["练习与总结"]],
        "content_rect_default": {"unit": "ratio", "x": 0.08, "y": 0.22, "w": 0.84, "h": 0.58},
        "slides": [
            {
                "title": "什么是勾股定理",
                "content": ["适用于直角三角形", "两直角边平方和等于斜边平方"],
                "content_blocks": [["适用于直角三角形", "两直角边平方和等于斜边平方"]],
                "notes": "",
                "layout_index": 1,
            },
            {
                "title": "公式与符号",
                "content": ["a² + b² = c²", "a、b 为直角边", "c 为斜边"],
                "content_blocks": [["a² + b² = c²", "a、b 为直角边", "c 为斜边"]],
                "notes": "",
                "layout_index": 1,
            },
            {
                "title": "经典例题",
                "content": ["已知 a=3, b=4", "求 c", "c=5"],
                "content_blocks": [["已知 a=3, b=4", "求 c", "c=5"]],
                "notes": "",
                "layout_index": 1,
            },
            {
                "title": "变式例题",
                "content": ["已知 c=13, a=5", "求 b", "b=12"],
                "content_blocks": [["已知 c=13, a=5", "求 b", "b=12"]],
                "notes": "",
                "layout_index": 1,
            },
            {
                "title": "常见误区",
                "content": ["先确认是直角三角形", "注意斜边对应最长边"],
                "content_blocks": [["先确认是直角三角形", "注意斜边对应最长边"]],
                "notes": "",
                "layout_index": 1,
            },
            {
                "title": "小结与练习",
                "content": ["牢记公式", "完成 2 道练习题巩固"],
                "content_blocks": [["牢记公式", "完成 2 道练习题巩固"]],
                "notes": "",
                "layout_index": 1,
            },
        ],
    }

    def _run(client: httpx.Client, base: str) -> tuple[Path, Path]:
        params = {"with_mp4": "true", "mp4_pages": "2", "mp4_max_wait_seconds": str(mp4_max_wait_seconds)}
        if mp4_portrait:
            params["mp4_portrait"] = mp4_portrait

        r = client.post(f"{base}/api/v1/generate/ppt/render", params=params, json=plan)
        if r.status_code != 200:
            raise SystemExit(f"ppt render failed: {r.status_code} {r.text}")
        resp = r.json()

        ppt_url = resp.get("download_url")
        job_id = resp.get("mp4_job_id")
        mp4_status_url = resp.get("mp4_status_url")
        mp4_pages_base_url = resp.get("mp4_pages_base_url")
        mp4_total_pages = int(resp.get("mp4_total_pages") or 0)
        if not ppt_url or not job_id or not mp4_status_url or not mp4_pages_base_url or mp4_total_pages != 2:
            raise SystemExit(f"missing mp4 fields: {resp}")

        ppt_path = out_dir / "pythagoras_6pages.pptx"
        dr = client.get(f"{base}{ppt_url}")
        dr.raise_for_status()
        ppt_path.write_bytes(dr.content)

        pages_dir = out_dir / "mp4_pages"
        pages_dir.mkdir(parents=True, exist_ok=True)

        deadline = time.time() + poll_timeout_s
        saved = set()
        while time.time() < deadline:
            rr = client.get(f"{base}{mp4_status_url}", timeout=30)
            rr.raise_for_status()
            meta = rr.json()
            status = meta.get("status")
            prog = meta.get("progress") or {}
            print(f"[*] mp4 status={status} progress={prog.get('done_pages')}/{prog.get('total_pages')}")

            pages = meta.get("pages") if isinstance(meta.get("pages"), dict) else {}
            for i in range(1, mp4_total_pages + 1):
                if i in saved:
                    continue
                st = pages.get(str(i)) if isinstance(pages.get(str(i)), dict) else {}
                if st.get("status") != "done":
                    continue
                url = f"{base}{mp4_pages_base_url}/{i}.mp4"
                out_path = pages_dir / f"page_{i}.mp4"
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
            time.sleep(poll_interval_s)

        return ppt_path, pages_dir

    from app.main import app
    from fastapi.testclient import TestClient

    tc = TestClient(app)
    with httpx.Client(base_url=str(tc.base_url), transport=tc._transport, timeout=180) as client:  # type: ignore[attr-defined]
        ppt_path, pages_dir = _run(client, str(tc.base_url))

    print("[+] pptx:", ppt_path)
    print("[+] mp4_pages:", pages_dir)


if __name__ == "__main__":
    main()

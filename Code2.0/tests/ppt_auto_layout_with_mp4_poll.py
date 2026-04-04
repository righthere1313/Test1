import os
import sys
import time
from pathlib import Path

import httpx


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(base_dir))

    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    timeout_s = int(os.getenv("POLL_TIMEOUT_SECONDS", "1800"))
    poll_interval = float(os.getenv("POLL_INTERVAL_SECONDS", "2"))

    payload = {
        "layout": os.getenv("LAYOUT", "general"),
        "source_text": os.getenv("SOURCE_TEXT", "请生成一份关于勾股定理的10页课件。"),
        "slides_total": int(os.getenv("SLIDES_TOTAL", "6")),
        "title": os.getenv("TITLE", "勾股定理"),
        "subtitle": os.getenv("SUBTITLE", ""),
        "with_mp4": True,
        "mp4_portrait": os.getenv("MP4_PORTRAIT") or None,
    }

    r = httpx.post(f"{base_url}/api/v1/generate/ppt/auto_layout", json=payload, timeout=60)
    r.raise_for_status()
    resp = r.json()
    print("[+] PPT generated:", resp.get("filename"))
    print("[+] PPT download_url:", resp.get("download_url"))

    job_id = resp.get("mp4_job_id")
    status_url = resp.get("mp4_status_url")
    mp4_url = resp.get("mp4_download_url")
    if not job_id or not status_url or not mp4_url:
        raise SystemExit("missing mp4 fields in response")

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        rr = httpx.get(f"{base_url}{status_url}", timeout=15)
        rr.raise_for_status()
        meta = rr.json()
        status = meta.get("status")
        prog = meta.get("progress") or {}
        print(f"[*] mp4 status={status}, progress={prog.get('done_pages')}/{prog.get('total_pages')}")
        if status == "done":
            break
        if status == "failed":
            raise SystemExit(f"mp4 failed: {meta.get('error')}")
        time.sleep(poll_interval)

    out_dir = base_dir / "tests" / "mp4_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{job_id}.mp4"

    with httpx.stream("GET", f"{base_url}{mp4_url}", timeout=600) as dr:
        dr.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in dr.iter_bytes(1024 * 256):
                if not chunk:
                    continue
                f.write(chunk)

    print("[+] mp4 saved:", out_path)


if __name__ == "__main__":
    main()

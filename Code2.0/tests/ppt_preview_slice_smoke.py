import os
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(base_dir))
    from app.main import app

    client = TestClient(app)

    payload = {
        "title": "预览切片测试",
        "subtitle": "smoke",
        "layout": "general",
        "slides": [
            {"title": "封面", "content": ["测试1", "测试2", "测试3"], "layout_index": 1},
            {"title": "第二页", "content": ["要点A", "要点B", "要点C"], "layout_index": 1},
            {"title": "第三页", "content": ["结论1", "结论2", "结论3"], "layout_index": 1},
        ],
    }

    r = client.post("/api/v1/generate/ppt/render", json=payload)
    if r.status_code != 200:
        raise SystemExit(f"generate ppt failed: {r.status_code} {r.text}")
    data = r.json()
    filename = data.get("filename")
    if not filename:
        raise SystemExit("missing filename")

    r = client.post("/api/v1/generate/ppt/preview", json={"filename": filename, "options": {"width": 1200, "include_thumbnails": True, "thumb_width": 300}})
    if r.status_code != 200:
        raise SystemExit(f"create preview failed: {r.status_code} {r.text}")
    meta = r.json()
    preview_id = meta.get("preview_id")
    if not preview_id:
        raise SystemExit("missing preview_id")

    status = meta.get("status")
    deadline = time.time() + 120
    while status not in {"done", "failed"} and time.time() < deadline:
        time.sleep(0.5)
        rr = client.get(f"/api/v1/generate/ppt/preview/{preview_id}")
        if rr.status_code != 200:
            raise SystemExit(f"poll preview failed: {rr.status_code} {rr.text}")
        meta = rr.json()
        status = meta.get("status")

    if status != "done":
        raise SystemExit(f"preview not done: {status} {meta.get('error')}")

    total_pages = int(meta.get("total_pages") or 0)
    if total_pages < 1:
        raise SystemExit(f"invalid total_pages: {total_pages}")

    r = client.get(f"/api/v1/generate/ppt/preview/{preview_id}/pages/1.png")
    if r.status_code != 200:
        raise SystemExit(f"page 1 fetch failed: {r.status_code} {r.text}")
    if not r.headers.get("content-type", "").startswith("image/png"):
        raise SystemExit(f"unexpected content-type: {r.headers.get('content-type')}")
    if len(r.content) < 1024:
        raise SystemExit("page 1 image too small")

    r = client.get(f"/api/v1/generate/ppt/preview/{preview_id}/thumbs/1.png")
    if r.status_code != 200:
        raise SystemExit(f"thumb 1 fetch failed: {r.status_code} {r.text}")
    if not r.headers.get("content-type", "").startswith("image/png"):
        raise SystemExit(f"unexpected content-type: {r.headers.get('content-type')}")
    if len(r.content) < 512:
        raise SystemExit("thumb 1 image too small")

    r = client.delete(f"/api/v1/generate/ppt/preview/{preview_id}")
    if r.status_code != 200:
        raise SystemExit(f"delete preview failed: {r.status_code} {r.text}")

    preview_dir = base_dir / "data" / "generated" / "ppt" / "previews" / preview_id
    if preview_dir.exists():
        raise SystemExit("preview dir not deleted")


if __name__ == "__main__":
    main()

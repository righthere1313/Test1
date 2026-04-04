import json
import os
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient


def _download(client: TestClient, url: str, out_path: Path) -> None:
    r = client.get(url)
    if r.status_code != 200:
        raise SystemExit(f"download failed: {r.status_code} {r.text}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(r.content)


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(base_dir))
    os.chdir(base_dir)

    from app.main import app
    from app.services.ppt_plan_store import PPTPlanStore

    out_dir = base_dir / "tests" / "e2e_outputs" / f"ppt_edit_doc_{int(time.time())}"
    out_dir.mkdir(parents=True, exist_ok=True)

    plan_dir = base_dir / "data" / "ppt_plans"
    plan_dir.mkdir(parents=True, exist_ok=True)

    client = TestClient(app)

    plan = {
        "title": "勾股定理",
        "subtitle": "初始版本（本地计划）",
        "template": None,
        "layout": "general",
        "cover_blocks": [["勾股定理"], ["自动生成"], ["测试用"]],
        "content_rect_default": {"x": 0.08, "y": 0.22, "w": 0.84, "h": 0.58},
        "slides": [
            {
                "title": "什么是勾股定理",
                "content": ["直角三角形", "两直角边平方和等于斜边平方"],
                "content_blocks": [["直角三角形", "两直角边平方和等于斜边平方"]],
                "notes": "",
                "layout_index": 1,
            },
            {
                "title": "公式与含义",
                "content": ["a²+b²=c²", "a,b为直角边", "c为斜边"],
                "content_blocks": [["a²+b²=c²", "a,b为直角边", "c为斜边"]],
                "notes": "",
                "layout_index": 1,
            },
            {
                "title": "经典例题",
                "content": ["已知两直角边3和4", "求斜边c", "c=5"],
                "content_blocks": [["已知两直角边3和4", "求斜边c", "c=5"]],
                "notes": "",
                "layout_index": 1,
            },
            {
                "title": "常见误区",
                "content": ["只能用于直角三角形", "先确认直角位置"],
                "content_blocks": [["只能用于直角三角形", "先确认直角位置"]],
                "notes": "",
                "layout_index": 1,
            },
            {
                "title": "总结与练习",
                "content": ["记住公式", "多做题巩固"],
                "content_blocks": [["记住公式", "多做题巩固"]],
                "notes": "",
                "layout_index": 1,
            },
        ],
    }

    store = PPTPlanStore()
    ppt_id, version, _ = store.create_project_with_version(layout="general", title=plan["title"], subtitle=plan["subtitle"], plan=plan)
    plan_path = plan_dir / f"{ppt_id}_v{version}.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    r = client.post("/api/v1/generate/ppt/render", json=plan)
    if r.status_code != 200:
        raise SystemExit(f"ppt render failed: {r.status_code} {r.text}")
    resp = r.json()
    download_url = resp.get("download_url")
    if not download_url:
        raise SystemExit(f"missing download_url: {resp}")

    v1_pptx = out_dir / f"{ppt_id}_v{version}.pptx"
    _download(client, download_url, v1_pptx)

    edit_req = {
        "ppt_id": ppt_id,
        "base_version": version,
        "session_id": None,
        "instructions": "patch edit",
        "patch": {
            "slide_index": 2,
            "title": "勾股定理：经典例题（已修改）",
            "content": ["我们来做一道经典题", "已知两直角边是3和4", "斜边就是5"],
        },
        "with_mp4": False,
    }
    r2 = client.post("/api/v1/generate/ppt", json=edit_req)
    if r2.status_code != 200:
        raise SystemExit(f"ppt edit failed: {r2.status_code} {r2.text}")
    resp2 = r2.json()
    version2 = int(resp2.get("version") or 0)
    download_url2 = resp2.get("download_url")
    if version2 != version + 1 or not download_url2:
        raise SystemExit(f"unexpected edit response: {resp2}")

    v2_pptx = out_dir / f"{ppt_id}_v{version2}.pptx"
    _download(client, download_url2, v2_pptx)

    print("ppt_id:", ppt_id)
    print("v1_pptx:", v1_pptx)
    print("v1_plan_json:", plan_path)
    print("v2_pptx:", v2_pptx)


if __name__ == "__main__":
    main()

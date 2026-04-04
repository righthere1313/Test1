import os
import time
from pathlib import Path

import httpx


def main() -> None:
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    layout = os.getenv("LAYOUT", "general")

    out_dir = Path(__file__).resolve().parents[1] / "tests" / "e2e_outputs" / f"ppt_edit_{int(time.time())}"
    out_dir.mkdir(parents=True, exist_ok=True)

    source_text = (
        "请生成一份关于勾股定理的课件，包含定义、证明思路、例题与总结。"
        "要求语言简洁，条理清晰。"
    )
    extra_instructions = (
        "必须至少包含一张图表。请在第2页（slides[1]）加入 chart 字段，严格按如下结构输出：\n"
        '{ "id":"bar_chart", "title":"例题类型分布", "subtitle":"勾股定理常见题型", "position":"right", "policy":"trim", '
        '"data": { "categories": ["直角三角形", "距离计算", "坐标几何", "实际应用", "综合题"], "values": [5, 3, 2, 4, 1] } }\n'
        "除该字段外其它字段按原有规则输出。"
    )

    with httpx.Client(timeout=180) as client:
        r1 = client.post(
            f"{base_url}/api/v1/generate/ppt/auto_layout",
            json={
                "layout": layout,
                "source_text": source_text,
                "slides_total": 8,
                "title": "勾股定理",
                "subtitle": "初始版本",
                "extra_instructions": extra_instructions,
                "with_mp4": False,
            },
        )
        if r1.status_code != 200:
            raise SystemExit(f"auto_layout failed: {r1.status_code} {r1.text}")
        a = r1.json()
        ppt_id = a.get("ppt_id")
        version = int(a.get("version") or 0)
        ppt_url = a.get("download_url")
        if not ppt_id or version < 1 or not ppt_url:
            raise SystemExit(f"missing ppt_id/version: {a}")

        p1 = out_dir / f"{ppt_id}_v{version}.pptx"
        with client.stream("GET", f"{base_url}{ppt_url}") as dr:
            dr.raise_for_status()
            with open(p1, "wb") as f:
                for chunk in dr.iter_bytes(1024 * 256):
                    if chunk:
                        f.write(chunk)

        r2 = client.post(
            f"{base_url}/api/v1/generate/ppt/edit",
            json={
                "ppt_id": ppt_id,
                "base_version": version,
                "session_id": None,
                "instructions": "把第3页的标题改为“勾股定理的经典例题”，并将整份课件的表述改得更口语化一些。",
                "with_mp4": False,
            },
        )
        if r2.status_code != 200:
            raise SystemExit(f"edit failed: {r2.status_code} {r2.text}")
        b = r2.json()
        v2 = int(b.get("version") or 0)
        ppt_url2 = b.get("download_url")
        if v2 != version + 1 or not ppt_url2:
            raise SystemExit(f"unexpected edit response: {b}")

        p2 = out_dir / f"{ppt_id}_v{v2}.pptx"
        with client.stream("GET", f"{base_url}{ppt_url2}") as dr2:
            dr2.raise_for_status()
            with open(p2, "wb") as f:
                for chunk in dr2.iter_bytes(1024 * 256):
                    if chunk:
                        f.write(chunk)

    print("[+] saved:", p1)
    print("[+] saved:", p2)


if __name__ == "__main__":
    main()


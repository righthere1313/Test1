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

    # 准备保存图片的本地目录
    save_dir = base_dir / "tests" / "preview_output"
    save_dir.mkdir(parents=True, exist_ok=True)
    print(f"[*] 预览图片将保存到: {save_dir}")

    payload = {
        "title": "预览切片测试",
        "subtitle": "将图片保存到本地",
        "layout": "general",
        "slides": [
            {"title": "封面", "content": ["这是第一页，测试预览效果", "包括标题、副标题和排版"], "layout_index": 1},
            {"title": "第二页: 核心功能", "content": ["1. 自动分页", "2. 高保真渲染", "3. 并发处理"], "layout_index": 1},
            {"title": "第三页: 总结", "content": ["测试通过后即可对接前端", "按页加载提升体验", "谢谢观看"], "layout_index": 1},
        ],
    }

    print("[*] 1. 正在生成 PPT...")
    r = client.post("/api/v1/generate/ppt/render", json=payload)
    if r.status_code != 200:
        raise SystemExit(f"generate ppt failed: {r.status_code} {r.text}")
    data = r.json()
    filename = data.get("filename")
    if not filename:
        raise SystemExit("missing filename")
    print(f"[+] PPT 生成成功: {filename}")

    print("[*] 2. 正在创建预览切片任务...")
    r = client.post("/api/v1/generate/ppt/preview", json={"filename": filename, "options": {"width": 1600, "include_thumbnails": True, "thumb_width": 400}})
    if r.status_code != 200:
        raise SystemExit(f"create preview failed: {r.status_code} {r.text}")
    meta = r.json()
    preview_id = meta.get("preview_id")
    if not preview_id:
        raise SystemExit("missing preview_id")
    print(f"[+] 预览任务创建成功，ID: {preview_id}")

    print("[*] 3. 正在等待渲染完成...")
    status = meta.get("status")
    deadline = time.time() + 120
    while status not in {"done", "failed"} and time.time() < deadline:
        time.sleep(1)
        rr = client.get(f"/api/v1/generate/ppt/preview/{preview_id}")
        if rr.status_code != 200:
            raise SystemExit(f"poll preview failed: {rr.status_code} {rr.text}")
        meta = rr.json()
        status = meta.get("status")
        progress = meta.get("progress", {})
        print(f"    - 状态: {status}, 进度: {progress.get('done_pages', 0)}/{progress.get('total_pages', '?')}")

    if status != "done":
        raise SystemExit(f"preview not done: {status} {meta.get('error')}")

    total_pages = int(meta.get("total_pages") or 0)
    print(f"[+] 渲染完成，共 {total_pages} 页")

    print("[*] 4. 正在下载并保存图片...")
    for i in range(1, total_pages + 1):
        # 下载高清大图
        r_page = client.get(f"/api/v1/generate/ppt/preview/{preview_id}/pages/{i}.png")
        if r_page.status_code == 200:
            page_path = save_dir / f"page_{i}_large.png"
            with open(page_path, "wb") as f:
                f.write(r_page.content)
            print(f"    - 已保存大图: {page_path.name} ({len(r_page.content) // 1024} KB)")
        else:
            print(f"    ! 下载大图失败: 第 {i} 页")

        # 下载缩略图
        r_thumb = client.get(f"/api/v1/generate/ppt/preview/{preview_id}/thumbs/{i}.png")
        if r_thumb.status_code == 200:
            thumb_path = save_dir / f"page_{i}_thumb.png"
            with open(thumb_path, "wb") as f:
                f.write(r_thumb.content)
            print(f"    - 已保存缩略图: {thumb_path.name} ({len(r_thumb.content) // 1024} KB)")
        else:
            print(f"    ! 下载缩略图失败: 第 {i} 页")

    # 注意：这里我们故意不调用 DELETE 接口删除资源，方便你后续在服务器上也去检查
    print("\n[✔] 测试完成！请前往 tests/preview_output 目录查看生成的图片。")


if __name__ == "__main__":
    main()

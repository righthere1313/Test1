import os
import time
from pathlib import Path

import httpx


def _download(client: httpx.Client, url: str, out_path: Path) -> None:
    r = client.get(url, timeout=600)
    r.raise_for_status()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(r.content)


def _write_debug(out_dir: Path, name: str, text: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    path.write_text(text, encoding="utf-8")


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    out_dir = base_dir / "tests" / "e2e_outputs" / f"auto_layout_ai_intro_{int(time.time())}"
    out_dir.mkdir(parents=True, exist_ok=True)

    base_url = os.getenv("BASE_URL", "").strip().rstrip("/")
    if not base_url:
        base_url = "http://127.0.0.1:8000"

    print("base_url:", base_url, flush=True)

    kb_seed = (
        "# 人工智能导论（知识库种子）\n\n"
        "人工智能（AI）研究如何让机器表现出智能行为，常见能力包括感知、学习、推理、规划、决策与生成。\n\n"
        "## 核心术语\n"
        "- 机器学习（ML）：从数据中学习映射关系与规律。\n"
        "- 深度学习（DL）：以多层神经网络为核心的机器学习方法。\n"
        "- 监督学习：用带标签数据训练分类/回归模型。\n"
        "- 无监督学习：发现聚类/降维等结构。\n"
        "- 强化学习：在交互环境中最大化长期回报。\n\n"
        "## 典型任务\n"
        "- 计算机视觉：分类、检测、分割、OCR。\n"
        "- 自然语言处理：文本分类、问答、信息抽取、机器翻译。\n"
        "- 多模态：图文/音视频联合理解与生成。\n\n"
        "## 评价与风险\n"
        "- 指标：准确率、召回率、F1、AUC、BLEU、ROUGE 等。\n"
        "- 风险：数据偏差、幻觉、隐私泄露、版权、对齐与安全。\n\n"
        "## 课程建议结构\n"
        "1. AI 发展与应用案例\n"
        "2. 学习范式：监督/无监督/强化\n"
        "3. 关键模型：线性模型、树模型、神经网络、Transformer\n"
        "4. 训练与泛化：损失函数、正则化、过拟合\n"
        "5. 实践流程：数据→特征→训练→评估→部署\n"
        "6. 伦理与安全\n"
    )

    document_id = None
    ppt_path = None
    try:
        with httpx.Client(base_url=base_url, timeout=300, trust_env=False) as client:
            files = {"file": ("ai_intro_seed.md", kb_seed.encode("utf-8"), "text/markdown")}
            r = client.post("/api/v1/files/upload/kb", files=files)
            _write_debug(out_dir, "kb_upload_response.txt", f"status={r.status_code}\n\n{r.text}\n")
            r.raise_for_status()
            kb_resp = r.json()
            document_id = kb_resp.get("document_id")

            req = {
                "source_text": "请制作一份《人工智能导论》课程课件，面向本科生，强调核心概念、学习范式、典型任务与伦理安全。",
                "slides_total": 15,
                "title": "人工智能导论",
                "subtitle": "15页课件（auto_layout）",
                "extra_instructions": "请尽量参考知识库内容，丰富每页要点，保证结构清晰、层层递进；每页要点不超过12行；加入1页课堂互动问题与1页小结。",
                "with_mp4": False,
            }
            r2 = client.post("/api/v1/generate/ppt/auto_layout", json=req)
            _write_debug(out_dir, "auto_layout_response.txt", f"status={r2.status_code}\n\n{r2.text}\n")
            r2.raise_for_status()
            resp = r2.json()
            download_url = resp.get("download_url")
            filename = resp.get("filename")
            if not download_url or not filename:
                raise SystemExit(f"missing download_url/filename: {resp}")

            ppt_path = out_dir / filename
            _download(client, download_url, ppt_path)
    except Exception as e:
        _write_debug(out_dir, "error.txt", repr(e))
        raise

    print("kb_document_id:", document_id)
    print("pptx:", ppt_path)


if __name__ == "__main__":
    main()

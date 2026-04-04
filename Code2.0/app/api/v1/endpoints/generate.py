import json
import os
import re
import threading
import uuid
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.schemas.generation import PPTPresentation, DocxDocument
from app.services.generator.ppt_generator import PPTGenerator
from app.services.generator.doc_generator import DocxGenerator
from app.services.ppt_preview import PPTPreviewOptions, PPTPreviewService
from app.services.mp4_service import MP4Options, MP4Service
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.ppt_plan_store import PPTPlanStore
from app.services.svg_layouts import extract_layout_content_rect, layout_exists, read_layout_design_spec, read_layout_svg
from app.services.text_wrap import max_chars_for_box, normalize_lines
from app.services.layout_plan_a import build_box_plan_plan_a

router = APIRouter()
ppt_generator = PPTGenerator()
docx_generator = DocxGenerator()
kb_service = KnowledgeBaseService()
ppt_preview_service = PPTPreviewService(root_dir=os.path.join(PPTGenerator.OUTPUT_DIR, "previews"))
mp4_service = MP4Service()
ppt_plan_store = PPTPlanStore()


class DocxAutoRequest(BaseModel):
    topic: str
    title: str | None = None
    extra_instructions: str | None = None


class PPTLayoutAutoRequest(BaseModel):
    layout: str = "general"
    source_text: str
    slides_total: int = 10
    title: str | None = None
    subtitle: str | None = None
    extra_instructions: str | None = None
    with_mp4: bool = False
    mp4_portrait: str | None = None
    mp4_max_wait_seconds: int | None = None
    mp4_pages: int | None = None


class PPTEditRequest(BaseModel):
    ppt_id: str
    base_version: int
    session_id: str | None = None
    instructions: str
    patch: dict | None = None
    title: str | None = None
    subtitle: str | None = None
    with_mp4: bool = False
    mp4_portrait: str | None = None
    mp4_max_wait_seconds: int | None = None
    mp4_pages: int | None = None


class PPTPreviewOptionsRequest(BaseModel):
    width: int = 1600
    include_thumbnails: bool = True
    thumb_width: int = 320
    format: str = "png"


class PPTPreviewRequest(BaseModel):
    filename: str
    options: PPTPreviewOptionsRequest | None = None


def _extract_json_object(text: str) -> dict:
    raw = (text or "").strip()
    if not raw:
        raise ValueError("empty answer")
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    import re

    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        raise ValueError("no json object found")
    obj = json.loads(m.group(0))
    if not isinstance(obj, dict):
        raise ValueError("json root is not object")
    return obj


def _normalize_ppt_plan(plan: dict, *, template_id: str, title: str, subtitle: str, slide_len: int, box_plan: dict) -> dict:
    plan = dict(plan or {})
    plan["template"] = str(template_id)

    if not str(plan.get("title") or "").strip():
        plan["title"] = title
    if subtitle and not str(plan.get("subtitle") or "").strip():
        plan["subtitle"] = subtitle
    elif "subtitle" not in plan:
        plan["subtitle"] = subtitle

    cover_blocks = plan.get("cover_blocks")
    normalized_cover = None
    if isinstance(cover_blocks, list):
        cover_specs = box_plan.get("cover_specs") if isinstance(box_plan.get("cover_specs"), list) else []
        normalized_cover = []
        for bi, b in enumerate(cover_blocks):
            if not isinstance(b, list):
                b = []
            sp = cover_specs[bi] if bi < len(cover_specs) and isinstance(cover_specs[bi], dict) else {}
            max_chars = max_chars_for_box(w_ratio=sp.get("w_ratio"), area_ratio=sp.get("area_ratio"), rank=bi + 1)
            lines = normalize_lines(b, max_chars=max_chars)
            normalized_cover.append(lines)
    plan["cover_blocks"] = normalized_cover

    slides = plan.get("slides")
    if not isinstance(slides, list):
        slides = []
    if len(slides) > int(slide_len):
        slides = slides[: int(slide_len)]
    while len(slides) < int(slide_len):
        slides.append({"title": f"第{len(slides)+1}页", "content": ["要点1", "要点2", "要点3"], "notes": "", "layout_index": 1})

    normalized_slides = []
    slide_specs_all = box_plan.get("slide_specs") if isinstance(box_plan.get("slide_specs"), list) else []
    for i, s in enumerate(slides, start=1):
        if not isinstance(s, dict):
            s = {}
        st = str(s.get("title") or "").strip() or f"第{i}页"

        content_blocks = s.get("content_blocks")
        normalized_blocks = None
        if isinstance(content_blocks, list):
            nb = []
            specs = slide_specs_all[i - 1] if (i - 1) < len(slide_specs_all) and isinstance(slide_specs_all[i - 1], list) else []
            for bi, b in enumerate(content_blocks):
                if not isinstance(b, list):
                    b = []
                sp = specs[bi] if bi < len(specs) and isinstance(specs[bi], dict) else {}
                max_chars = max_chars_for_box(w_ratio=sp.get("w_ratio"), area_ratio=sp.get("area_ratio"), rank=bi + 1)
                lines = normalize_lines(b, max_chars=max_chars)
                nb.append(lines)
            normalized_blocks = nb

        flat = []
        if normalized_blocks:
            for b in normalized_blocks:
                flat.extend(b)
        if not flat:
            content = s.get("content")
            if not isinstance(content, list):
                content = []
            flat = normalize_lines(content, max_chars=42)

        if len(flat) < 3:
            flat.extend(["要点1", "要点2", "要点3"])
        if len(flat) > 18:
            flat = flat[:18]

        chart = s.get("chart") if isinstance(s, dict) else None
        normalized_slides.append(
            {
                "title": st,
                "content": flat,
                "content_blocks": normalized_blocks,
                "notes": str(s.get("notes") or ""),
                "layout_index": int(s.get("layout_index") or 1),
                "chart": chart,
            }
        )

    plan["slides"] = normalized_slides

    if isinstance(plan.get("cover_blocks"), list) and isinstance(box_plan.get("cover_blocks"), int):
        need = int(box_plan["cover_blocks"])
        cur = plan["cover_blocks"]
        if len(cur) < need:
            plan["cover_blocks"] = cur + ([[]] * (need - len(cur)))
        elif len(cur) > need:
            plan["cover_blocks"] = cur[:need]

    if isinstance(box_plan.get("slide_blocks"), list):
        need_list = box_plan["slide_blocks"]
        for idx, slide in enumerate(plan.get("slides") or []):
            need = int(need_list[idx]) if idx < len(need_list) else None
            if need is None:
                continue
            blocks = slide.get("content_blocks")
            if not isinstance(blocks, list):
                continue
            if len(blocks) < need:
                slide["content_blocks"] = blocks + ([[]] * (need - len(blocks)))
            elif len(blocks) > need:
                slide["content_blocks"] = blocks[:need]

    return plan


def _cap_plan_a_lines(plan: dict, max_lines: int = 12) -> dict:
    if not isinstance(plan, dict):
        return plan
    max_lines = max(1, int(max_lines))
    slides = plan.get("slides")
    if not isinstance(slides, list):
        return plan
    for s in slides:
        if not isinstance(s, dict):
            continue
        blocks = s.get("content_blocks")
        if isinstance(blocks, list) and blocks:
            b0 = blocks[0]
            if isinstance(b0, list) and len(b0) > max_lines:
                blocks[0] = b0[:max_lines]
        content = s.get("content")
        if isinstance(content, list) and len(content) > max_lines:
            s["content"] = content[:max_lines]
    return plan


def _build_plan_a_fallback(
    *,
    query: str,
    slide_len: int,
    box_plan: dict,
    title: str,
    subtitle: str,
    extra_instructions: str | None,
    kb_results: list[dict] | None,
) -> dict:
    import re

    q = str(query or "").strip()
    inst = str(extra_instructions or "").strip()

    slide_len = max(1, int(slide_len))
    max_lines = 12

    candidates: list[str] = []
    for item in kb_results or []:
        content = item.get("content") if isinstance(item, dict) else None
        if not isinstance(content, str):
            continue
        text = content.replace("\r", "\n")
        parts = re.split(r"[\n。！？!?；;]+", text)
        for p in parts:
            s = str(p).strip()
            if not s:
                continue
            if len(s) < 6:
                continue
            if len(s) > 120:
                s = s[:120]
            candidates.append(s)

    seen: set[str] = set()
    deduped: list[str] = []
    for s in candidates:
        k = re.sub(r"\s+", " ", s)
        if k in seen:
            continue
        seen.add(k)
        deduped.append(k)

    outline = [
        "课程目标与学习路径",
        "AI 概览：定义与发展",
        "机器学习：基本流程",
        "监督学习：分类与回归",
        "无监督学习：聚类与降维",
        "强化学习：交互与回报",
        "深度学习与神经网络",
        "Transformer 与大模型",
        "计算机视觉：典型任务",
        "自然语言处理：典型任务",
        "多模态与生成式 AI",
        "评估指标与实验设计",
        "应用案例与部署落地",
        "伦理、安全与合规",
        "课堂互动：思考题",
        "小结与延伸阅读",
    ]
    while len(outline) < slide_len:
        outline.append(f"主题扩展 {len(outline) + 1}")
    outline = outline[:slide_len]

    slides: list[dict] = []
    cursor = 0
    for idx in range(slide_len):
        st = outline[idx]
        lines: list[str] = []
        if idx == 0:
            lines.extend(
                [
                    "了解 AI/ML/DL 的关系与常见应用",
                    "掌握监督/无监督/强化三种学习范式",
                    "了解训练-评估-部署的基本工程流程",
                    "建立对风险与伦理安全的基本认识",
                ]
            )
        if "课堂互动" in st:
            lines.extend(
                [
                    "问题1：你认为“智能”最关键的能力是什么？为什么？",
                    "问题2：数据偏差会如何影响模型决策？举例说明。",
                    "问题3：大模型的“幻觉”在产品中如何缓解？",
                ]
            )
        if "小结" in st:
            lines.extend(
                [
                    "回顾：概念→范式→模型→评估→应用→风险",
                    "建议：从小项目入手，形成完整闭环",
                    "延伸：阅读 1-2 篇经典论文或课程笔记",
                ]
            )

        while len(lines) < max_lines and cursor < len(deduped):
            lines.append(deduped[cursor])
            cursor += 1

        if inst:
            if "不要" in inst and len(lines) > 10:
                lines = lines[:10]

        slides.append(
            {
                "title": st,
                "content": normalize_lines(lines, max_chars=42)[:max_lines],
                "content_blocks": [normalize_lines(lines, max_chars=42)[:max_lines]],
                "notes": "",
                "layout_index": 1,
            }
        )

    cover_blocks = [[title], [subtitle], ["自动生成"]]
    return {
        "title": title,
        "subtitle": subtitle,
        "template": "",
        "cover_blocks": cover_blocks,
        "slides": slides,
    }


def _ensure_required_sections(doc: dict) -> dict:
    title = str(doc.get("title") or "").strip()
    if not title:
        title = "教案"
    elements = doc.get("elements")
    if not isinstance(elements, list):
        elements = []
    required = ["教学目标", "教学过程", "教学方法", "课堂活动设计", "课后作业"]
    existing = set()
    for el in elements:
        if isinstance(el, dict) and el.get("type") == "heading":
            existing.add(str(el.get("content") or "").strip())
    for name in required:
        if name in existing:
            continue
        elements.append({"type": "heading", "content": name, "level": 1})
        elements.append({"type": "paragraph", "content": "（由大模型补充）", "level": 1})
    return {"title": title, "elements": elements}

@router.post("/ppt/render", response_model=dict)
async def generate_ppt_render(
    data: PPTPresentation,
    background_tasks: BackgroundTasks,
    with_mp4: bool = False,
    mp4_portrait: str | None = None,
    mp4_max_wait_seconds: int | None = None,
    mp4_pages: int | None = None,
):
    try:
        file_path = ppt_generator.generate(data)
        filename = os.path.basename(file_path)
        resp = {
            "status": "success",
            "filename": filename,
            "download_url": f"/api/v1/generate/download/ppt/{filename}"
        }
        if with_mp4:
            job_id = mp4_service.create_job_id()
            slides = []
            for s in getattr(data, "slides", []) or []:
                slides.append({"title": getattr(s, "title", ""), "content": getattr(s, "content", []), "notes": getattr(s, "notes", "")})
            limit = int(mp4_pages) if mp4_pages else None
            if limit is not None and limit < 1:
                raise HTTPException(status_code=400, detail="mp4_pages must be >= 1")
            slides_sel = slides[:limit] if limit else slides
            mp4_service.init_meta(job_id=job_id, total_pages=len(slides_sel))
            options = MP4Options(portrait_path=mp4_portrait, max_wait_seconds=int(mp4_max_wait_seconds) if mp4_max_wait_seconds else MP4Options.max_wait_seconds)
            threading.Thread(target=mp4_service.run, kwargs={"job_id": job_id, "slides": slides_sel, "options": options}, daemon=True).start()
            resp.update(
                {
                    "mp4_status": "queued",
                    "mp4_job_id": job_id,
                    "mp4_mode": "per_page",
                    "mp4_total_pages": len(slides_sel),
                    "mp4_pages_base_url": f"/api/v1/generate/ppt/mp4/{job_id}/pages",
                    "mp4_status_url": f"/api/v1/generate/ppt/mp4/{job_id}",
                }
            )
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _merge_text_only_plan(base_plan: dict, new_plan: dict) -> dict:
    base = dict(base_plan or {})
    upd = new_plan if isinstance(new_plan, dict) else {}
    out = dict(base)

    if str(upd.get("title") or "").strip():
        out["title"] = str(upd.get("title") or "")
    if "subtitle" in upd:
        out["subtitle"] = upd.get("subtitle")

    if isinstance(upd.get("cover_blocks"), list):
        out["cover_blocks"] = upd.get("cover_blocks")

    base_slides = base.get("slides") if isinstance(base.get("slides"), list) else []
    upd_slides = upd.get("slides") if isinstance(upd.get("slides"), list) else []
    merged_slides = []
    for idx, bs in enumerate(base_slides):
        bsd = bs if isinstance(bs, dict) else {}
        usd = upd_slides[idx] if idx < len(upd_slides) and isinstance(upd_slides[idx], dict) else {}
        sd = dict(bsd)
        if str(usd.get("title") or "").strip():
            sd["title"] = str(usd.get("title") or "")
        if "notes" in usd:
            sd["notes"] = str(usd.get("notes") or "")
        if isinstance(usd.get("content"), list):
            sd["content"] = usd.get("content")
        if isinstance(usd.get("content_blocks"), list):
            sd["content_blocks"] = usd.get("content_blocks")
        merged_slides.append(sd)
    out["slides"] = merged_slides
    return out


def _build_text_patch_plan(base_plan: dict, patch: dict) -> dict:
    p = patch if isinstance(patch, dict) else {}
    slide_index = p.get("slide_index")
    if slide_index is None:
        raise ValueError("patch.slide_index is required")
    idx = int(slide_index)
    if idx < 1:
        raise ValueError("patch.slide_index must be >= 1")

    base_slides = base_plan.get("slides") if isinstance(base_plan.get("slides"), list) else []
    if idx > len(base_slides):
        raise ValueError("patch.slide_index out of range")

    slides = [{} for _ in range(len(base_slides))]
    item = {}
    if "title" in p:
        item["title"] = p.get("title")
    if "notes" in p:
        item["notes"] = p.get("notes")
    if "content" in p:
        item["content"] = p.get("content")
    if "content_blocks" in p:
        item["content_blocks"] = p.get("content_blocks")
    slides[idx - 1] = item

    out = {"slides": slides}
    if "title" in p:
        out["title"] = p.get("title")
    if "subtitle" in p:
        out["subtitle"] = p.get("subtitle")
    if "cover_blocks" in p:
        out["cover_blocks"] = p.get("cover_blocks")
    return out


@router.post("/ppt/edit", response_model=dict)
async def edit_ppt(req: PPTEditRequest, background_tasks: BackgroundTasks):
    ppt_id = str(req.ppt_id or "").strip()
    if not ppt_id:
        raise HTTPException(status_code=400, detail="ppt_id is required")
    base_version = int(req.base_version)

    proj = ppt_plan_store.get_project(ppt_id)
    if not proj:
        raise HTTPException(status_code=404, detail="ppt_id not found")
    if int(proj.get("current_version") or 0) != base_version:
        raise HTTPException(status_code=409, detail="base_version mismatch")

    base_plan = ppt_plan_store.get_plan(ppt_id, version=base_version)
    if not base_plan:
        raise HTTPException(status_code=404, detail="plan not found")

    edited_raw = None
    if req.patch is not None:
        try:
            edited_raw = _build_text_patch_plan(base_plan, req.patch)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        session_msgs = ppt_plan_store.get_session_messages(req.session_id or "", limit=20) if req.session_id else []
        prompt = (
            "你是PPT文本修改助手。你将收到：对话历史、原始PPT JSON（渲染前计划）、以及新的修改要求。\n"
            "目标：只修改文本内容，不修改任何版式/布局/样式字段；输出一个JSON对象，结构必须与原始PPT JSON完全兼容。\n"
            "\n"
            "硬性规则（必须遵守）：\n"
            "- 只允许改写字段：title, subtitle, cover_blocks, slides[*].title, slides[*].notes, slides[*].content, slides[*].content_blocks。\n"
            "- 严禁改写/新增/删除任何非文本字段（如 layout/layout_index/content_rect_default/background_* / image_* / chart 等必须保持不变）。\n"
            "- slides 数量必须保持不变；每页 content_blocks 的结构保持不变。\n"
            "- 所有字符串严禁包含 \\n 或 \\r；需要换行时必须拆成数组多个元素。\n"
            "- 输出仅包含一个JSON对象，不要解释文字，不要代码块。\n"
            "\n"
            "对话历史（从旧到新，可能为空）：\n"
            "{history}\n"
            "\n"
            "新的修改要求：\n"
            "{instructions}\n"
            "\n"
            "原始PPT JSON：\n"
            "{plan}\n"
        ).format(
            history=json.dumps(session_msgs, ensure_ascii=False),
            instructions=str(req.instructions or "").strip(),
            plan=json.dumps(base_plan, ensure_ascii=False),
        )

        try:
            result = kb_service.answer(prompt, top_k=3, document_id=None, temporary_document_ids=None, session_id=None)
            answer = (result or {}).get("answer") or ""
            edited_raw = _extract_json_object(answer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"edit llm failed: {e}")

    merged = _merge_text_only_plan(base_plan, edited_raw)
    if req.title and str(req.title).strip():
        merged["title"] = str(req.title).strip()
    if req.subtitle is not None:
        merged["subtitle"] = str(req.subtitle or "")

    layout_name = str(merged.get("layout") or "").strip() or str(proj.get("layout") or "").strip()
    merged["layout"] = layout_name

    slides_total = 1 + len(merged.get("slides") if isinstance(merged.get("slides"), list) else [])
    rect = merged.get("content_rect_default")
    if rect is None:
        raise HTTPException(status_code=400, detail="content_rect_default is required")
    box_plan = build_box_plan_plan_a(rect, slides_total)
    merged = _normalize_ppt_plan(
        merged,
        template_id="",
        title=str(merged.get("title") or ""),
        subtitle=str(merged.get("subtitle") or ""),
        slide_len=len(merged.get("slides") if isinstance(merged.get("slides"), list) else []),
        box_plan=box_plan,
    )
    merged = _cap_plan_a_lines(merged, max_lines=12)
    if isinstance(merged, dict):
        merged["template"] = None
        merged["layout"] = layout_name

    try:
        data = PPTPresentation.model_validate(merged)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"invalid edited plan: {e}")

    try:
        new_ver, _ = ppt_plan_store.create_new_version(
            ppt_id=ppt_id,
            base_version=base_version,
            plan=merged,
            session_id=req.session_id,
            instructions=req.instructions,
        )
    except ValueError as e:
        msg = str(e)
        if "base_version mismatch" in msg:
            raise HTTPException(status_code=409, detail="base_version mismatch")
        if "ppt_id not found" in msg:
            raise HTTPException(status_code=404, detail="ppt_id not found")
        raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"db error: {e}")

    try:
        file_path = ppt_generator.generate(data)
        filename = os.path.basename(file_path)
        ppt_plan_store.set_rendered_filename(ppt_id=ppt_id, version=int(new_ver), filename=filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"render failed: {e}")

    resp = {
        "status": "success",
        "ppt_id": ppt_id,
        "version": int(new_ver),
        "filename": filename,
        "download_url": f"/api/v1/generate/download/ppt/{filename}",
    }

    if bool(req.with_mp4):
        job_id = mp4_service.create_job_id()
        slides = []
        for s in merged.get("slides") if isinstance(merged, dict) else []:
            if isinstance(s, dict):
                slides.append({"title": s.get("title") or "", "content": s.get("content") or [], "notes": s.get("notes") or ""})
        limit = int(req.mp4_pages) if req.mp4_pages else None
        if limit is not None and limit < 1:
            raise HTTPException(status_code=400, detail="mp4_pages must be >= 1")
        slides_sel = slides[:limit] if limit else slides
        mp4_service.init_meta(job_id=job_id, total_pages=len(slides_sel))
        options = MP4Options(
            portrait_path=req.mp4_portrait,
            max_wait_seconds=int(req.mp4_max_wait_seconds) if req.mp4_max_wait_seconds else MP4Options.max_wait_seconds,
        )
        threading.Thread(target=mp4_service.run, kwargs={"job_id": job_id, "slides": slides_sel, "options": options}, daemon=True).start()
        resp.update(
            {
                "mp4_status": "queued",
                "mp4_job_id": job_id,
                "mp4_mode": "per_page",
                "mp4_total_pages": len(slides_sel),
                "mp4_pages_base_url": f"/api/v1/generate/ppt/mp4/{job_id}/pages",
                "mp4_status_url": f"/api/v1/generate/ppt/mp4/{job_id}",
            }
        )

    return resp


@router.post("/ppt", response_model=dict)
async def edit_ppt_alias(req: PPTEditRequest, background_tasks: BackgroundTasks):
    return await edit_ppt(req, background_tasks)


@router.post("/ppt/preview", response_model=dict)
async def create_ppt_preview(req: PPTPreviewRequest, background_tasks: BackgroundTasks):
    filename = os.path.basename((req.filename or "").strip())
    if not filename:
        raise HTTPException(status_code=400, detail="filename is required")
    pptx_path = os.path.join(PPTGenerator.OUTPUT_DIR, filename)
    if not os.path.abspath(pptx_path).startswith(os.path.abspath(PPTGenerator.OUTPUT_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(pptx_path):
        raise HTTPException(status_code=404, detail="File not found")

    opt_req = req.options or PPTPreviewOptionsRequest()
    fmt = str(opt_req.format or "").strip().lower() or "png"
    if fmt != "png":
        raise HTTPException(status_code=400, detail="format only supports png")

    width = max(320, int(opt_req.width))
    include_thumbnails = bool(opt_req.include_thumbnails)
    thumb_width = max(160, int(opt_req.thumb_width))
    options = PPTPreviewOptions(width=width, include_thumbnails=include_thumbnails, thumb_width=thumb_width, image_format=fmt)

    try:
        total_pages = ppt_preview_service.get_slide_count(pptx_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read pptx: {e}")

    preview_id = ppt_preview_service.create_preview_id()
    meta = ppt_preview_service.init_meta(preview_id=preview_id, filename=filename, total_pages=total_pages, options=options)
    threading.Thread(target=ppt_preview_service.run, kwargs={"preview_id": preview_id, "pptx_path": pptx_path, "options": options}, daemon=True).start()
    return meta


@router.get("/ppt/preview/{preview_id}", response_model=dict)
async def get_ppt_preview(preview_id: str):
    if not ppt_preview_service.is_valid_preview_id(preview_id):
        raise HTTPException(status_code=404, detail="Preview not found")
    meta = ppt_preview_service.load_meta(preview_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Preview not found")
    base = f"/api/v1/generate/ppt/preview/{preview_id}"
    meta = dict(meta)
    meta["pages_base_url"] = f"{base}/pages"
    meta["thumbs_base_url"] = f"{base}/thumbs"
    return meta


@router.get("/ppt/preview/{preview_id}/pages/{page}.png")
async def get_ppt_preview_page(preview_id: str, page: int):
    if not ppt_preview_service.is_valid_preview_id(preview_id):
        raise HTTPException(status_code=404, detail="Preview not found")
    if int(page) < 1:
        raise HTTPException(status_code=400, detail="Invalid page")
    
    pages_dir = ppt_preview_service.pages_dir(preview_id)
    preview_dir = ppt_preview_service.preview_dir(preview_id)
    
    image_path = None
    try:
        names = os.listdir(pages_dir)
        patterns = [
            f"page-{int(page):02d}.png",
            f"page-{int(page):01d}.png",
            f"page-{int(page):03d}.png"
        ]
        for pattern in patterns:
            if pattern in names:
                image_path = os.path.join(pages_dir, pattern)
                break
        if not image_path:
            for name in names:
                m = re.fullmatch(r"page-0*(\d+)\.png", name)
                if m and m.group(1) == str(int(page)):
                    image_path = os.path.join(pages_dir, name)
                    break
    except Exception:
        pass
    
    if not image_path:
        image_path = ppt_preview_service.page_image_path(preview_id, page)
    
    if not os.path.abspath(image_path).startswith(os.path.abspath(preview_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(image_path, media_type="image/png", filename=os.path.basename(image_path))


@router.get("/ppt/preview/{preview_id}/thumbs/{page}.png")
async def get_ppt_preview_thumb(preview_id: str, page: int):
    if not ppt_preview_service.is_valid_preview_id(preview_id):
        raise HTTPException(status_code=404, detail="Preview not found")
    if int(page) < 1:
        raise HTTPException(status_code=400, detail="Invalid page")
    
    thumbs_dir = ppt_preview_service.thumbs_dir(preview_id)
    preview_dir = ppt_preview_service.preview_dir(preview_id)
    
    image_path = None
    try:
        names = os.listdir(thumbs_dir)
        patterns = [
            f"page-{int(page):02d}.png",
            f"page-{int(page):01d}.png",
            f"page-{int(page):03d}.png"
        ]
        for pattern in patterns:
            if pattern in names:
                image_path = os.path.join(thumbs_dir, pattern)
                break
        if not image_path:
            for name in names:
                m = re.fullmatch(r"page-0*(\d+)\.png", name)
                if m and m.group(1) == str(int(page)):
                    image_path = os.path.join(thumbs_dir, name)
                    break
    except Exception:
        pass
    
    if not image_path:
        image_path = ppt_preview_service.thumb_image_path(preview_id, page)
    
    if not os.path.abspath(image_path).startswith(os.path.abspath(preview_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(image_path, media_type="image/png", filename=os.path.basename(image_path))


@router.delete("/ppt/preview/{preview_id}", response_model=dict)
async def delete_ppt_preview(preview_id: str):
    if not ppt_preview_service.is_valid_preview_id(preview_id):
        raise HTTPException(status_code=404, detail="Preview not found")
    meta = ppt_preview_service.load_meta(preview_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Preview not found")
    ppt_preview_service.delete_preview(preview_id)
    return {"status": "deleted", "preview_id": preview_id}

@router.post("/ppt/multipart", response_model=dict)
async def generate_ppt_multipart(
    background_tasks: BackgroundTasks,
    payload: str = Form(...),
    images: list[UploadFile] = File(default=[]),
    with_mp4: bool = Form(False),
    mp4_portrait: str | None = Form(None),
    mp4_max_wait_seconds: int | None = Form(None),
    mp4_pages: int | None = Form(None),
):
    try:
        raw = json.loads(payload)
        data = PPTPresentation.model_validate(raw)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    image_map: dict[str, str] = {}
    upload_dir = os.path.join(PPTGenerator.OUTPUT_DIR, "uploads", uuid.uuid4().hex)
    os.makedirs(upload_dir, exist_ok=True)
    try:
        for image in images:
            name = os.path.basename(image.filename or "")
            if not name:
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext not in {".png", ".jpg", ".jpeg"}:
                continue
            save_path = os.path.join(upload_dir, f"{uuid.uuid4().hex}{ext}")
            content = await image.read()
            with open(save_path, "wb") as f:
                f.write(content)
            image_map[name] = save_path

        file_path = ppt_generator.generate(data, image_files=image_map)
        filename = os.path.basename(file_path)
        resp = {
            "status": "success",
            "filename": filename,
            "download_url": f"/api/v1/generate/download/ppt/{filename}",
        }
        if with_mp4:
            job_id = mp4_service.create_job_id()
            slides = []
            for s in getattr(data, "slides", []) or []:
                slides.append({"title": getattr(s, "title", ""), "content": getattr(s, "content", []), "notes": getattr(s, "notes", "")})
            limit = int(mp4_pages) if mp4_pages else None
            if limit is not None and limit < 1:
                raise HTTPException(status_code=400, detail="mp4_pages must be >= 1")
            slides_sel = slides[:limit] if limit else slides
            mp4_service.init_meta(job_id=job_id, total_pages=len(slides_sel))
            options = MP4Options(portrait_path=mp4_portrait, max_wait_seconds=int(mp4_max_wait_seconds) if mp4_max_wait_seconds else MP4Options.max_wait_seconds)
            threading.Thread(target=mp4_service.run, kwargs={"job_id": job_id, "slides": slides_sel, "options": options}, daemon=True).start()
            resp.update(
                {
                    "mp4_status": "queued",
                    "mp4_job_id": job_id,
                    "mp4_mode": "per_page",
                    "mp4_total_pages": len(slides_sel),
                    "mp4_pages_base_url": f"/api/v1/generate/ppt/mp4/{job_id}/pages",
                    "mp4_status_url": f"/api/v1/generate/ppt/mp4/{job_id}",
                }
            )
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ppt/auto_layout", response_model=dict)
async def generate_ppt_auto_layout(req: PPTLayoutAutoRequest, background_tasks: BackgroundTasks):
    source_text = (req.source_text or "").strip()
    if not source_text:
        raise HTTPException(status_code=400, detail="source_text is required")
    layout_name = (req.layout or "").strip()
    if not layout_name:
        layout_name = "general"
    if not layout_exists(layout_name):
        raise HTTPException(status_code=400, detail="layout not found")
    slides_total = max(2, int(req.slides_total))
    slide_len = slides_total - 1

    content_rect_default = extract_layout_content_rect(layout_name, "03_content.svg")
    if content_rect_default is None:
        content_rect_default = extract_layout_content_rect(layout_name)
    if content_rect_default is None:
        raise HTTPException(status_code=400, detail="layout svg has no CONTENT_AREA")

    box_plan = build_box_plan_plan_a(content_rect_default, slides_total)
    design_spec = read_layout_design_spec(layout_name) or ""
    cover_svg = ""
    content_svg = ""
    try:
        cover_svg = read_layout_svg(layout_name, "01_cover.svg")
    except Exception:
        cover_svg = ""
    try:
        content_svg = read_layout_svg(layout_name, "03_content.svg")
    except Exception:
        content_svg = ""
    title = (req.title or "").strip() or "课件"
    subtitle = (req.subtitle or "").strip()

    prompt = (
        "你是 PPT Master（方案A：layout模板 + 单栏12行）。请只输出一个JSON对象，不要输出任何解释文字，不要代码块。\n"
        "任务：根据源文本自动扩写并分页，输出可被后端渲染的PPT JSON（渲染端按行写入文本框，不依赖自动换行）。\n"
        "\n"
        "输出JSON Schema（必须遵守）：\n"
        "- 顶层必须包含：title, subtitle, template, slides。\n"
        f"- slides长度必须是{slide_len}（总页数含封面为{slides_total}）。\n"
        "- slides[i]必须包含：title, content(字符串数组), content_blocks(二维数组), notes, layout_index。\n"
        "\n"
        "版式与容量（方案A固定规则）：\n"
        "- 每页只使用一个大文本框：slides[i].content_blocks 的长度必须为 1。\n"
        "- content_blocks[0] 为“逐行内容数组”，每个字符串代表一行；每页最多 12 行。\n"
        "- 严禁在任意字符串内包含 \\n 或 \\r；长句必须拆成多行（拆成多个字符串）。\n"
        "- 行长上限：max_chars = clamp(10, round(10 + 70*w_ratio), 42)，其中 w_ratio 来自 specs。\n"
        "- slides[i].content 必须是 content_blocks[0] 的拷贝/汇总（同样逐行）。\n"
        "- layout_index 固定填 1。\n"
        "\n"
        "源文本：\n"
        "{source}\n"
        "\n"
        "layout设计规范（用于理解风格与口吻）：\n"
        "{design_spec}\n"
        "\n"
        "layout封面SVG（仅用于理解风格，不要复述）：\n"
        "{cover_svg}\n"
        "\n"
        "layout内容页SVG（仅用于理解CONTENT_AREA与风格，不要复述）：\n"
        "{content_svg}\n"
        "\n"
        "文本框计划与规格（必须严格匹配）：\n"
        "{box_plan}\n"
        "\n"
        "内容区矩形（ratio，给渲染器对齐；无需改写）：\n"
        "{content_rect}\n"
    ).format(
        source=source_text,
        design_spec=(design_spec[:4000] if design_spec else ""),
        cover_svg=(cover_svg[:6000] if cover_svg else ""),
        content_svg=(content_svg[:6000] if content_svg else ""),
        box_plan=json.dumps(box_plan, ensure_ascii=False),
        content_rect=json.dumps(content_rect_default, ensure_ascii=False),
    )
    if req.extra_instructions:
        prompt += f"\n额外要求：{req.extra_instructions.strip()}\n"

    try:
        if getattr(kb_service, "llm", None) is None:
            kb_service.llm = kb_service._build_llm()  # type: ignore[attr-defined]
        if getattr(kb_service, "llm", None) is None:
            raise HTTPException(
                status_code=503,
                detail="LLM is not configured. Set DASHSCOPE_API_KEY (Qwen/Tongyi) or OPENAI_* env vars before calling auto_layout.",
            )
        try:
            result = kb_service.answer(
                prompt,
                top_k=3,
                document_id=None,
                temporary_document_ids=None,
                session_id=f"ppt-auto-layout-{uuid.uuid4().hex}",
                require_llm=True,
            )
        except RuntimeError as e:
            raise HTTPException(status_code=502, detail=str(e))
        answer = (result or {}).get("answer") or ""
        if isinstance(answer, str) and answer.strip().startswith("基于检索重排结果"):
            raise HTTPException(status_code=502, detail="LLM was not used (unexpected extractive answer returned).")
        try:
            plan_raw = _extract_json_object(answer)
        except Exception:
            snippet = (answer or "")[:800]
            raise HTTPException(status_code=502, detail=f"LLM did not return a JSON object. answer_snippet={snippet!r}")
        plan = _normalize_ppt_plan(
            plan_raw,
            template_id="",
            title=title,
            subtitle=subtitle,
            slide_len=slide_len,
            box_plan=box_plan,
        )
        plan = _cap_plan_a_lines(plan, max_lines=12)
        if isinstance(plan, dict):
            plan["template"] = None
            plan["layout"] = layout_name
            plan.setdefault("content_rect_default", content_rect_default)
        data = PPTPresentation.model_validate(plan)
        ppt_id = None
        version = None
        try:
            ppt_id, version, _ = ppt_plan_store.create_project_with_version(
                layout=layout_name,
                title=str(getattr(data, "title", "") or ""),
                subtitle=str(getattr(data, "subtitle", "") or "") or None,
                plan=plan,
                session_id=None,
                instructions=str(req.extra_instructions or "") or None,
            )
        except Exception:
            ppt_id = None
            version = None
        file_path = ppt_generator.generate(data)
        filename = os.path.basename(file_path)
        if ppt_id and version:
            try:
                ppt_plan_store.set_rendered_filename(ppt_id=ppt_id, version=int(version), filename=filename)
            except Exception:
                pass
        resp = {
            "status": "success",
            "filename": filename,
            "download_url": f"/api/v1/generate/download/ppt/{filename}",
            "llm_used": True,
        }
        if ppt_id and version:
            resp["ppt_id"] = ppt_id
            resp["version"] = int(version)
        if bool(req.with_mp4):
            job_id = mp4_service.create_job_id()
            slides = []
            for s in plan.get("slides") if isinstance(plan, dict) else []:
                if isinstance(s, dict):
                    slides.append({"title": s.get("title") or "", "content": s.get("content") or [], "notes": s.get("notes") or ""})
            limit = int(req.mp4_pages) if req.mp4_pages else None
            if limit is not None and limit < 1:
                raise HTTPException(status_code=400, detail="mp4_pages must be >= 1")
            slides_sel = slides[:limit] if limit else slides
            mp4_service.init_meta(job_id=job_id, total_pages=len(slides_sel))
            options = MP4Options(
                portrait_path=req.mp4_portrait,
                max_wait_seconds=int(req.mp4_max_wait_seconds) if req.mp4_max_wait_seconds else MP4Options.max_wait_seconds,
            )
            threading.Thread(target=mp4_service.run, kwargs={"job_id": job_id, "slides": slides_sel, "options": options}, daemon=True).start()
            resp.update(
                {
                    "mp4_status": "queued",
                    "mp4_job_id": job_id,
                    "mp4_mode": "per_page",
                    "mp4_total_pages": len(slides_sel),
                    "mp4_pages_base_url": f"/api/v1/generate/ppt/mp4/{job_id}/pages",
                    "mp4_status_url": f"/api/v1/generate/ppt/mp4/{job_id}",
                }
            )
        return resp
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ppt/mp4/{job_id}", response_model=dict)
async def get_ppt_mp4_status(job_id: str):
    meta = mp4_service.load_meta(job_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Job not found")
    meta = dict(meta)
    meta["mp4_mode"] = "per_page"
    meta["mp4_pages_base_url"] = f"/api/v1/generate/ppt/mp4/{job_id}/pages"
    return meta


@router.get("/ppt/mp4/{job_id}/pages/{page}.mp4")
async def get_ppt_mp4_page(job_id: str, page: int):
    if int(page) < 1:
        raise HTTPException(status_code=400, detail="Invalid page")
    meta = mp4_service.load_meta(job_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Job not found")
    total_pages = int(meta.get("total_pages") or 0)
    if total_pages and int(page) > total_pages:
        raise HTTPException(status_code=404, detail="Page not found")
    video_path = mp4_service.page_video_path(job_id, page)
    job_dir = mp4_service.job_dir(job_id)
    if not os.path.abspath(video_path).startswith(os.path.abspath(job_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(video_path, media_type="video/mp4", filename=os.path.basename(video_path))


@router.post("/docx", response_model=dict)
async def generate_docx(data: DocxDocument):
    try:
        file_path = docx_generator.generate(data)
        filename = os.path.basename(file_path)
        return {
            "status": "success",
            "filename": filename,
            "download_url": f"/api/v1/generate/download/docx/{filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/docx/auto", response_model=dict)
async def generate_docx_auto(req: DocxAutoRequest):
    topic = (req.topic or "").strip()
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")
    title = (req.title or f"{topic}教案").strip()
    prompt = (
        "你是一名教案撰写助手。请输出一个用于后端生成DOCX的JSON（只输出JSON，不要任何解释文字）。\n"
        "JSON结构必须是：{title, elements}。\n"
        "elements是数组，每个元素必须包含：type, content, level。\n"
        "type只能是：heading, paragraph, bullet, numbered。\n"
        "必须包含以下章节标题（用 heading，level=1）：教学目标、教学过程、教学方法、课堂活动设计、课后作业。\n"
        "每个章节至少包含2条 bullet 或 numbered，内容尽量具体可执行，避免空泛。\n"
        f"主题：{topic}\n"
        f"标题：{title}\n"
    )
    if req.extra_instructions:
        prompt += f"\n额外要求：{req.extra_instructions.strip()}\n"
    try:
        result = kb_service.answer(prompt, top_k=3, document_id=None, temporary_document_ids=None, session_id=f"docx-auto-{uuid.uuid4().hex}")
        answer = (result or {}).get("answer") or ""
        raw = _extract_json_object(answer)
        raw = _ensure_required_sections(raw)
        data = DocxDocument.model_validate(raw)
        file_path = docx_generator.generate(data)
        filename = os.path.basename(file_path)
        return {
            "status": "success",
            "filename": filename,
            "download_url": f"/api/v1/generate/download/docx/{filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{file_type}/{filename}")
async def download_file(file_type: str, filename: str):
    if file_type not in ["ppt", "docx", "video"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    if file_type == "ppt":
        directory = PPTGenerator.OUTPUT_DIR
        media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    elif file_type == "docx":
        directory = DocxGenerator.OUTPUT_DIR
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        directory = MP4Service.OUTPUT_DIR
        media_type = "video/mp4"
        
    file_path = os.path.join(directory, filename)
    
    # Security check: Ensure file is within the directory
    if not os.path.abspath(file_path).startswith(os.path.abspath(directory)):
         raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(file_path, media_type=media_type, filename=filename)

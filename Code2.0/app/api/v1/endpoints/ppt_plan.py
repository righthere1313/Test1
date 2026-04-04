import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel
import hashlib
import zipfile
import xml.etree.ElementTree as ET

from app.schemas.generation import PPTPresentation
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.ppt_template_parser import parse_ppt_template
from app.api.v1.endpoints.templates import _safe_resolve_template_path


router = APIRouter()
kb_service = KnowledgeBaseService()


class PPTPlanRequest(BaseModel):
    template: str
    topic: str
    slides_total: int = 10
    extra_instructions: Optional[str] = None


def _assets_dir() -> Path:
    return Path("data/generated/ppt/assets").resolve()


def _extract_template_slide_background_candidates(template_path: Path) -> List[Dict[str, Any]]:
    out_dir = _assets_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates: list[dict] = []
    try:
        with zipfile.ZipFile(str(template_path), "r") as zf:
            slide_nums = []
            for name in zf.namelist():
                if not name.startswith("ppt/slides/slide") or not name.endswith(".xml"):
                    continue
                stem = Path(name).stem
                num = stem.replace("slide", "")
                if num.isdigit():
                    slide_nums.append(int(num))
            slide_nums = sorted(set(slide_nums))
            if not slide_nums:
                return []

            media_sizes: dict[str, int] = {}
            for name in zf.namelist():
                if not name.startswith("ppt/media/"):
                    continue
                suffix = Path(name).suffix.lower()
                if suffix not in {".png", ".jpg", ".jpeg"}:
                    continue
                try:
                    media_sizes[name] = int(zf.getinfo(name).file_size)
                except Exception:
                    media_sizes[name] = 0

            for num in slide_nums:
                slide_name = f"ppt/slides/slide{num}.xml"
                rels_name = f"ppt/slides/_rels/slide{num}.xml.rels"

                rels_map: dict[str, str] = {}
                try:
                    rels_xml = zf.read(rels_name)
                    root = ET.fromstring(rels_xml)
                    for rel in root.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
                        r_id = rel.attrib.get("Id")
                        target = rel.attrib.get("Target")
                        r_type = rel.attrib.get("Type") or ""
                        if not r_id or not target:
                            continue
                        if "/image" not in r_type:
                            continue
                        if target.startswith("../"):
                            target = "ppt/" + target.replace("../", "", 1)
                        elif target.startswith("media/"):
                            target = "ppt/" + target
                        elif target.startswith("/"):
                            target = target.lstrip("/")
                        rels_map[r_id] = target
                except Exception:
                    rels_map = {}

                targets = set()
                try:
                    slide_xml = zf.read(slide_name)
                    root = ET.fromstring(slide_xml)
                    for blip in root.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip"):
                        for k, v in blip.attrib.items():
                            if k.endswith("}embed") and v:
                                t = rels_map.get(v)
                                if t:
                                    targets.add(t)
                except Exception:
                    targets = set()

                best_target = None
                best_size = 0
                for t in targets:
                    size = media_sizes.get(t, 0)
                    if size > best_size:
                        best_size = size
                        best_target = t
                if not best_target:
                    continue
                try:
                    blob = zf.read(best_target)
                except Exception:
                    continue
                ext = Path(best_target).suffix.lstrip(".") or "png"
                key = hashlib.md5(blob).hexdigest()[:16]
                out_path = out_dir / f"tpl_bg_{key}.{ext}"
                if not out_path.exists():
                    try:
                        out_path.write_bytes(blob)
                    except Exception:
                        continue
                candidates.append(
                    {
                        "id": f"slide{num}",
                        "slide_number": num,
                        "image_path": str(out_path),
                        "size_bytes": best_size,
                    }
                )
    except Exception:
        return []

    seen = set()
    deduped = []
    for c in candidates:
        p = c.get("image_path")
        if not p or p in seen:
            continue
        seen.add(p)
        deduped.append(c)
    return deduped


def _extract_template_slide_background_parts(template_path: Path, max_slides: int = 12, max_parts_per_slide: int = 24) -> List[Dict[str, Any]]:
    out_dir = _assets_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    parts: list[dict] = []
    try:
        with zipfile.ZipFile(str(template_path), "r") as zf:
            slide_files = []
            for name in zf.namelist():
                if not name.startswith("ppt/slides/slide") or not name.endswith(".xml"):
                    continue
                stem = Path(name).stem
                num = stem.replace("slide", "")
                if num.isdigit():
                    slide_files.append((int(num), name))
            slide_files.sort()
            slide_files = slide_files[: max(1, int(max_slides))]
            if not slide_files:
                return []

            media_sizes: dict[str, int] = {}
            for name in zf.namelist():
                if not name.startswith("ppt/media/"):
                    continue
                suffix = Path(name).suffix.lower()
                if suffix not in {".png", ".jpg", ".jpeg"}:
                    continue
                try:
                    media_sizes[name] = int(zf.getinfo(name).file_size)
                except Exception:
                    media_sizes[name] = 0

            for num, slide_name in slide_files:
                rels_name = f"ppt/slides/_rels/slide{num}.xml.rels"
                rels_map: dict[str, str] = {}
                try:
                    rels_xml = zf.read(rels_name)
                    root = ET.fromstring(rels_xml)
                    for rel in root.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
                        r_id = rel.attrib.get("Id")
                        target = rel.attrib.get("Target")
                        r_type = rel.attrib.get("Type") or ""
                        if not r_id or not target:
                            continue
                        if "/image" not in r_type:
                            continue
                        if target.startswith("../"):
                            target = "ppt/" + target.replace("../", "", 1)
                        elif target.startswith("media/"):
                            target = "ppt/" + target
                        elif target.startswith("/"):
                            target = target.lstrip("/")
                        rels_map[r_id] = target
                except Exception:
                    rels_map = {}

                try:
                    slide_xml = zf.read(slide_name)
                    root = ET.fromstring(slide_xml)
                except Exception:
                    continue

                ns = {
                    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
                    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
                    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
                }
                pics = root.findall(".//p:pic", ns)
                for pic in pics[: max(1, int(max_parts_per_slide))]:
                    embed = None
                    try:
                        blip = pic.find(".//a:blip", ns)
                        if blip is not None:
                            embed = blip.attrib.get(f"{{{ns['r']}}}embed")
                    except Exception:
                        embed = None
                    target = rels_map.get(embed or "")
                    if not target:
                        continue
                    suffix = Path(target).suffix.lower()
                    if suffix not in {".png", ".jpg", ".jpeg"}:
                        continue

                    x = y = cx = cy = None
                    try:
                        xfrm = pic.find(".//a:xfrm", ns)
                        off = xfrm.find("a:off", ns) if xfrm is not None else None
                        ext = xfrm.find("a:ext", ns) if xfrm is not None else None
                        if off is not None:
                            x = off.attrib.get("x")
                            y = off.attrib.get("y")
                        if ext is not None:
                            cx = ext.attrib.get("cx")
                            cy = ext.attrib.get("cy")
                    except Exception:
                        x = y = cx = cy = None
                    if not (x and y and cx and cy):
                        continue

                    try:
                        blob = zf.read(target)
                    except Exception:
                        continue
                    ext_out = Path(target).suffix.lstrip(".") or "png"
                    key = hashlib.md5(blob).hexdigest()[:16]
                    out_path = out_dir / f"tpl_part_{key}.{ext_out}"
                    if not out_path.exists():
                        try:
                            out_path.write_bytes(blob)
                        except Exception:
                            continue

                    parts.append(
                        {
                            "slide_number": num,
                            "image_path": str(out_path),
                            "x": int(x),
                            "y": int(y),
                            "w": int(cx),
                            "h": int(cy),
                            "unit": "emu",
                            "size_bytes": media_sizes.get(target, 0),
                        }
                    )
    except Exception:
        return []

    return parts


def _extract_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise ValueError("empty response")
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("no json object found in response")
    data = json.loads(m.group(0))
    if not isinstance(data, dict):
        raise ValueError("json root is not object")
    return data


def _fallback_plan(template_path: Path, topic: str, slides_total: int) -> Dict[str, Any]:
    slide_n = max(2, int(slides_total)) - 1
    def mk(title: str, points: List[str]) -> Dict[str, Any]:
        return {"title": title, "content": points[:6], "notes": "", "layout_index": 1}

    base = [
        mk("目录", ["1. 定理表述", "2. 符号与条件", "3. 例题", "4. 应用", "5. 总结与练习"]),
        mk("定理表述", ["直角三角形两直角边 a、b，斜边 c", "勾股定理：a² + b² = c²", "c = √(a² + b²)"]),
        mk("符号与条件", ["前提：必须是直角三角形", "a、b 为直角边", "c 为斜边（对着直角）"]),
        mk("例题：3-4-5", ["已知 a=3, b=4", "c=√(9+16)=5", "3-4-5 为常见勾股数组"]),
        mk("变式：求直角边", ["已知 c 与 a", "b=√(c²-a²)", "注意 c>a"]),
        mk("应用：对角线", ["矩形长 a 宽 b", "对角线 d=√(a²+b²)", "工程测量 3-4-5 拉线法"]),
        mk("距离公式", ["AB=√((x₂-x₁)²+(y₂-y₁)²)", "来自水平差与竖直差", "连接解析几何"]),
        mk("总结与练习", ["核心：a²+b²=c²", "会算：已知两边求第三边", "练习：给出3道题"]),
    ]
    slides = (base + [mk("拓展", ["勾股定理与面积", "勾股数与整数解", "拓展阅读"])])[:slide_n]
    while len(slides) < slide_n:
        slides.append(mk(f"补充{len(slides)+1}", ["要点1", "要点2", "要点3"]))
    return {"title": f"{topic}（课件）", "subtitle": "模板学习（fallback）", "template": str(template_path), "slides": slides}


@router.post("/plan", response_model=dict)
async def plan_ppt(req: PPTPlanRequest) -> Dict[str, Any]:
    template_path = _safe_resolve_template_path(req.template)
    slides_total = max(2, int(req.slides_total))
    slide_len = slides_total - 1
    template_struct = parse_ppt_template(template_path, max_slides=min(6, slide_len), max_shapes_per_slide=60, max_text_len=280)
    layout_schema = {
        "template_name": template_struct.get("template_name"),
        "slide_width": template_struct.get("slide_width"),
        "slide_height": template_struct.get("slide_height"),
        "layout_count": template_struct.get("layout_count"),
        "layouts": template_struct.get("layouts"),
        "slides": template_struct.get("slides"),
    }
    bg_candidates = _extract_template_slide_background_candidates(template_path)
    bg_parts = _extract_template_slide_background_parts(template_path)
    run_id = str(int(time.time()))

    bg_lines = "\n".join([f"- {i}: {c['image_path']} (from {c['id']})" for i, c in enumerate(bg_candidates[:24])])
    parts_lines = "\n".join(
        [
            f"- slide={p['slide_number']}, image_path={p['image_path']}, x={p['x']}, y={p['y']}, w={p['w']}, h={p['h']}"
            for p in bg_parts[:60]
        ]
    )
    prompt = (
        "你是 PPT Master（单次生成模式）。你的任务是：在一次输出中，直接生成可被后端渲染的PPT JSON。\n"
        "全局纪律：\n"
        "- 严禁提问、严禁多轮对话、严禁输出解释文字；只允许输出一个JSON对象。\n"
        "- JSON必须可被 json.loads 直接解析（不要Markdown代码块、不要多余前后缀）。\n"
        "\n"
        "输出JSON Schema（必须遵守）：\n"
        "- 顶层必须包含：title, subtitle, slides, template。\n"
        "- 顶层允许包含：background_image（封面单图背景）、background_parts_default（封面分块背景）。\n"
        "- slides为数组，长度必须是{slide_len}（总页数含封面为{slides_total}）。\n"
        "- slides[i]必须包含：title, content, notes, layout_index。\n"
        "- slides[i]允许包含：background_image 或 background_parts。\n"
        "\n"
        "模板学习（严格模式）：\n"
        "- 你必须先解析我提供的“模板布局JSON流”，严格按其中 layouts[].placeholders 的数量与几何(left/top/width/height)选择 layout_index。\n"
        "- 不得编造任何新的layout_index；不得输出不在模板JSON流中的layout_index。\n"
        "- 需要图文页时：选择 placeholders 中更适合承载图片/正文的布局（placeholder多、内容区更大者优先）。\n"
        "\n"
        "背景规则：\n"
        "- 优先使用分块背景：background_parts_default（封面）与 slides[i].background_parts（每页）。\n"
        "- background_parts 每个元素必须包含：image_path, x, y, w, h, unit, z。\n"
        "- image_path 必须从我提供的“背景分块候选列表”里原样选择；unit 固定填写 emu；x/y/w/h 必须原样复用候选的数值；z 从小到大叠放。\n"
        "- 如果你选择单图背景，则 background_image 必须从“背景候选列表”里选择 image_path。\n"
        "\n"
        "内容规则：\n"
        "- 主题：{topic}。用于课堂教学。\n"
        "- content为字符串数组，每页3-6条要点；每条尽量1-2句，包含：前提、推导要点、一个数值例子、以及一句反思/提问。\n"
        "- 页面结构建议：目录、定理表述、证明思路、例题、应用、总结与练习（可按模板能力调整）。\n"
        "- 换行规则：content 中每个字符串代表一行；字符串内禁止包含\\n/\\r；长句必须拆成多行（拆成多个元素）。\n"
        "- 行长建议：单行尽量<=36字；小框/侧边栏位更短（<=12字）或留空。\n"
        "\n"
        "输出前自检（在心里完成，不要输出自检文本）：\n"
        "- slides长度正确；每页字段齐全；layout_index均存在于模板JSON流；背景引用均来自候选；JSON无多余文本。\n"
        "\n"
        "template 字段必须填写模板编号：{template}\n"
        "\n"
        "模板布局JSON流（请严格学习其排版参数）：\n"
        "{layout_json}\n"
        "\n"
        "背景候选列表（用于 background_image）：\n"
        "{bg_lines}\n"
        "\n"
        "背景分块候选列表（用于 background_parts）：\n"
        "{parts_lines}\n"
    ).format(
        slide_len=slide_len,
        slides_total=slides_total,
        topic=req.topic,
        template=str(req.template),
        layout_json=json.dumps(layout_schema, ensure_ascii=False),
        bg_lines=bg_lines,
        parts_lines=parts_lines,
    )
    if req.extra_instructions:
        prompt += f"\n额外要求：{req.extra_instructions.strip()}\n"

    try:
        result = kb_service.answer(prompt, top_k=3, document_id=None, temporary_document_ids=None, session_id=f"ppt-plan-{run_id}")
        answer = (result or {}).get("answer") or ""
        plan = _extract_json(answer)
        plan["template"] = str(req.template)
        plan.setdefault("title", f"{req.topic}（课件）")
        plan.setdefault("subtitle", f"模板学习 {template_path.name}")
        slides = plan.get("slides")
        if not isinstance(slides, list):
            raise ValueError("slides is not a list")
        if len(slides) > slide_len:
            plan["slides"] = slides[:slide_len]
        elif len(slides) < slide_len:
            while len(plan["slides"]) < slide_len:
                plan["slides"].append({"title": f"补充{len(plan['slides'])+1}", "content": ["要点1", "要点2", "要点3"], "notes": "", "layout_index": 1})
        PPTPresentation.model_validate(plan)
        return {"plan": plan, "mode": "llm"}
    except Exception:
        plan = _fallback_plan(template_path, req.topic, slides_total)
        if bg_candidates:
            bg = bg_candidates[0].get("image_path")
            if bg:
                plan["background_image"] = bg
                for s in plan.get("slides", []) if isinstance(plan.get("slides"), list) else []:
                    if isinstance(s, dict):
                        s.setdefault("background_image", bg)
        return {"plan": plan, "mode": "fallback"}

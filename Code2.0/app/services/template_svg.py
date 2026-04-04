from __future__ import annotations

from typing import Any, Dict, List


def _xml_escape(s: str) -> str:
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _shape_area(shp: Dict[str, Any]) -> int:
    try:
        return int(shp.get("width") or 0) * int(shp.get("height") or 0)
    except Exception:
        return 0


def template_struct_to_svg_bundle(
    template_struct: Dict[str, Any],
    *,
    max_slides: int = 6,
    max_shapes_per_slide: int = 60,
    max_text_len: int = 80,
) -> str:
    sw = int(template_struct.get("slide_width") or 1280)
    sh = int(template_struct.get("slide_height") or 720)
    slides = template_struct.get("slides") if isinstance(template_struct.get("slides"), list) else []

    parts: List[str] = []
    parts.append(f"<SVG_META slide_width='{sw}' slide_height='{sh}' viewBox='0 0 {sw} {sh}'/>")

    for si, slide in enumerate(slides[: max(0, int(max_slides))]):
        if not isinstance(slide, dict):
            continue
        shapes = slide.get("shapes") if isinstance(slide.get("shapes"), list) else []
        kept = []
        for shp in shapes[: max(0, int(max_shapes_per_slide))]:
            if not isinstance(shp, dict):
                continue
            if not all(k in shp for k in ("left", "top", "width", "height")):
                continue
            kept.append(shp)

        ranked_text = [s for s in kept if s.get("kind") == "text"]
        ranked_text.sort(key=_shape_area, reverse=True)
        rank_map = {}
        for i, shp in enumerate(ranked_text, start=1):
            key = (int(shp.get("left") or 0), int(shp.get("top") or 0), int(shp.get("width") or 0), int(shp.get("height") or 0))
            if key not in rank_map:
                rank_map[key] = i

        parts.append(f"<SVG_SLIDE index='{si}'>")
        parts.append(f"<svg xmlns='http://www.w3.org/2000/svg' width='{sw}' height='{sh}' viewBox='0 0 {sw} {sh}'>")
        parts.append("<rect x='0' y='0' width='100%' height='100%' fill='white'/>")

        for shp in kept:
            try:
                x = int(shp.get("left") or 0)
                y = int(shp.get("top") or 0)
                w = max(1, int(shp.get("width") or 1))
                h = max(1, int(shp.get("height") or 1))
            except Exception:
                continue

            kind = str(shp.get("kind") or "shape")
            key = (x, y, w, h)
            rank = rank_map.get(key, 0)
            stroke = "#2E75B6" if kind == "text" else "#999999"
            parts.append(
                f"<rect x='{x}' y='{y}' width='{w}' height='{h}' fill='none' stroke='{stroke}' stroke-width='2'/>"
            )
            label = f"{kind}"
            if rank:
                label += f" r{rank}"
            text_preview = ""
            if kind == "text":
                raw_text = str(shp.get("text") or "").strip().replace("\n", " ")
                if raw_text:
                    text_preview = raw_text[: max(0, int(max_text_len))]
            if text_preview:
                label += f": {text_preview}"
            if label:
                parts.append(
                    f"<text x='{x + 6}' y='{y + 18}' font-size='16' fill='{stroke}'>{_xml_escape(label)}</text>"
                )

        parts.append("</svg>")
        parts.append("</SVG_SLIDE>")

    return "\n".join(parts)


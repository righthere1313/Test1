from __future__ import annotations

from typing import Any, Dict, Optional


def build_box_plan_plan_a(content_rect_default: Optional[Dict[str, Any]], slides_total: int) -> Dict[str, Any]:
    rect = content_rect_default if isinstance(content_rect_default, dict) else {}
    try:
        x = float(rect.get("x") or 0.05)
        y = float(rect.get("y") or 0.12)
        w = float(rect.get("w") or 0.9)
        h = float(rect.get("h") or 0.75)
    except Exception:
        x, y, w, h = 0.05, 0.12, 0.9, 0.75
    x = max(0.0, min(0.98, x))
    y = max(0.0, min(0.98, y))
    w = max(0.02, min(1.0 - x, w))
    h = max(0.02, min(1.0 - y, h))
    area_ratio = float(w) * float(h)

    slide_len = max(1, int(slides_total) - 2)
    slide_blocks = [1 for _ in range(slide_len)]
    spec = {
        "rank": 1,
        "area_ratio": round(area_ratio, 6),
        "left_ratio": round(x, 6),
        "top_ratio": round(y, 6),
        "w_ratio": round(w, 6),
        "h_ratio": round(h, 6),
    }
    slide_specs = [[spec] for _ in range(slide_len)]
    return {"cover_blocks": 0, "slide_blocks": slide_blocks, "cover_specs": [], "slide_specs": slide_specs}

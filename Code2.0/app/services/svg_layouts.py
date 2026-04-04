from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET


def _templates_root() -> Path:
    possible_paths = [
        Path(__file__).resolve().parents[3] / "ppt模版",
        Path(__file__).resolve().parents[2] / "ppt模版",
        Path("/ppt模版"),
        Path("/app/ppt模版"),
    ]
    for path in possible_paths:
        if path.exists() and path.is_dir():
            return path
    return possible_paths[0]


def _layouts_root() -> Path:
    return (_templates_root() / "layouts").resolve()


def list_layout_names() -> List[str]:
    root = _layouts_root()
    try:
        return sorted([p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")])
    except Exception:
        return []


def layout_exists(layout_name: str) -> bool:
    name = (layout_name or "").strip()
    if not name:
        return False
    try:
        root = _layouts_root()
        p = (root / name).resolve()
        return str(p).startswith(str(root)) and p.exists() and p.is_dir()
    except Exception:
        return False


def _safe_resolve_layout_svg(layout_name: str, svg_name: str) -> Path:
    root = _layouts_root()
    name = (layout_name or "").strip()
    if not name:
        raise ValueError("layout_name is required")
    svg = (svg_name or "").strip()
    if not svg:
        raise ValueError("svg_name is required")
    p = (root / name / svg).resolve()
    if not str(p).startswith(str(root)):
        raise ValueError("layout path is not allowed")
    if p.suffix.lower() != ".svg":
        raise ValueError("layout svg must be .svg")
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(str(p))
    return p


def _parse_viewbox(root: ET.Element) -> Tuple[float, float]:
    vb = (root.get("viewBox") or "").strip()
    if vb:
        parts = vb.replace(",", " ").split()
        if len(parts) >= 4:
            try:
                return float(parts[2]), float(parts[3])
            except Exception:
                pass
    try:
        w = float((root.get("width") or "1280").replace("px", "").strip())
        h = float((root.get("height") or "720").replace("px", "").strip())
        return w, h
    except Exception:
        return 1280.0, 720.0


def _tag_name(el: ET.Element) -> str:
    tag = el.tag or ""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _iter_text_elements(root: ET.Element):
    for el in root.iter():
        if _tag_name(el) != "text":
            continue
        yield el


def _iter_rect_elements(root: ET.Element):
    for el in root.iter():
        if _tag_name(el) != "rect":
            continue
        yield el


def _float_attr(el: ET.Element, key: str, default: float = 0.0) -> float:
    raw = (el.get(key) or "").strip()
    if not raw:
        return default
    raw = raw.replace("px", "")
    try:
        return float(raw)
    except Exception:
        return default


def _rect_tuple(el: ET.Element) -> Tuple[float, float, float, float]:
    x = _float_attr(el, "x", 0.0)
    y = _float_attr(el, "y", 0.0)
    w = _float_attr(el, "width", 0.0)
    h = _float_attr(el, "height", 0.0)
    return x, y, w, h


def _rect_contains(rect: Tuple[float, float, float, float], pt: Tuple[float, float]) -> bool:
    x, y, w, h = rect
    px, py = pt
    return px >= x and py >= y and px <= (x + w) and py <= (y + h)


def _rect_area(rect: Tuple[float, float, float, float]) -> float:
    return max(0.0, rect[2]) * max(0.0, rect[3])


def extract_content_rect_from_svg(svg_path: Path) -> Optional[Dict[str, Any]]:
    try:
        root = ET.parse(str(svg_path)).getroot()
    except Exception:
        return None

    vw, vh = _parse_viewbox(root)
    vw = max(1.0, float(vw))
    vh = max(1.0, float(vh))

    token = "CONTENT_AREA"
    target_pt: Optional[Tuple[float, float]] = None
    for t in _iter_text_elements(root):
        s = "".join(list(t.itertext()) or []).strip()
        if token in s:
            x = _float_attr(t, "x", 0.0)
            y = _float_attr(t, "y", 0.0)
            target_pt = (x, y)
            break

    rects = []
    for r in _iter_rect_elements(root):
        rect = _rect_tuple(r)
        if rect[2] <= 0 or rect[3] <= 0:
            continue
        if rect[0] == 0 and rect[1] == 0 and abs(rect[2] - vw) < 0.01 and abs(rect[3] - vh) < 0.01:
            continue
        rects.append((rect, r))

    best: Optional[Tuple[float, float, float, float]] = None
    if target_pt is not None:
        candidates: list[Tuple[Tuple[float, float, float, float], ET.Element]] = [
            (rect, el) for rect, el in rects if _rect_contains(rect, target_pt)
        ]
        if candidates:
            dashed = [rect for rect, el in candidates if (el.get("stroke-dasharray") or "").strip()]
            if dashed:
                best = max(dashed, key=_rect_area)
            else:
                best = max((rect for rect, _ in candidates), key=_rect_area)

    if best is None:
        dashed = []
        for rect, el in rects:
            if (el.get("stroke-dasharray") or "").strip():
                dashed.append(rect)
        if dashed:
            best = max(dashed, key=_rect_area)

    if best is None and rects:
        best = max((rect for rect, _ in rects), key=_rect_area)

    if best is None:
        return None

    x, y, w, h = best
    return {"x": x / vw, "y": y / vh, "w": w / vw, "h": h / vh, "unit": "ratio"}


def _pick_best_svg_for_content_area(layout_dir: Path) -> Optional[Path]:
    if not layout_dir.exists() or not layout_dir.is_dir():
        return None
    preferred = ["03_content.svg", "02_chapter.svg", "01_cover.svg", "02_toc.svg", "04_ending.svg"]
    for name in preferred:
        p = layout_dir / name
        if p.exists() and p.is_file():
            if extract_content_rect_from_svg(p) is not None:
                return p
    for p in sorted(layout_dir.glob("*.svg")):
        if p.is_file() and extract_content_rect_from_svg(p) is not None:
            return p
    return None


def extract_layout_content_rect(layout_name: str, svg_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    root = _layouts_root()
    name = (layout_name or "").strip()
    if not name:
        return None
    layout_dir = (root / name).resolve()
    if not str(layout_dir).startswith(str(root)) or not layout_dir.exists() or not layout_dir.is_dir():
        return None
    if svg_name:
        try:
            p = _safe_resolve_layout_svg(name, svg_name)
        except Exception:
            p = None
        if p is not None:
            return extract_content_rect_from_svg(p)
        return None
    picked = _pick_best_svg_for_content_area(layout_dir)
    if picked is None:
        return None
    return extract_content_rect_from_svg(picked)


def read_layout_svg(layout_name: str, svg_name: str) -> str:
    p = _safe_resolve_layout_svg(layout_name, svg_name)
    return p.read_text(encoding="utf-8", errors="ignore")


def read_layout_design_spec(layout_name: str) -> Optional[str]:
    root = _layouts_root()
    name = (layout_name or "").strip()
    if not name:
        return None
    p = (root / name / "design_spec.md").resolve()
    if not str(p).startswith(str(root)):
        return None
    if not p.exists() or not p.is_file():
        return None
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


def list_all_covers() -> List[Dict[str, Any]]:
    root = _layouts_root()
    covers = []
    try:
        for layout_dir in root.iterdir():
            if not layout_dir.is_dir() or layout_dir.name.startswith("."):
                continue
            cover_path = layout_dir / "01_cover.svg"
            if cover_path.exists() and cover_path.is_file():
                try:
                    svg = cover_path.read_text(encoding="utf-8", errors="ignore")
                    covers.append({
                        "layout": layout_dir.name,
                        "name": "01_cover.svg",
                        "svg": svg
                    })
                except Exception:
                    continue
    except Exception:
        pass
    return covers

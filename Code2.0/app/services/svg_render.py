from __future__ import annotations

import hashlib
import io
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class SvgTextStyle:
    x: float
    y: float
    font_size_px: float
    font_family: str
    fill: str
    bold: bool
    anchor: str


_TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def _tag_name(el: ET.Element) -> str:
    tag = el.tag or ""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


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


def _float_attr(el: ET.Element, key: str, default: float = 0.0) -> float:
    raw = (el.get(key) or "").strip()
    if not raw:
        return default
    raw = raw.replace("px", "")
    try:
        return float(raw)
    except Exception:
        return default


def _str_attr(el: ET.Element, key: str, default: str = "") -> str:
    return str(el.get(key) or default).strip()


def _parse_bold(el: ET.Element) -> bool:
    w = _str_attr(el, "font-weight", "").lower()
    if "bold" in w:
        return True
    try:
        return int(float(w)) >= 600
    except Exception:
        return False


def extract_svg_token_styles(svg_text: str) -> Dict[str, Tuple[SvgTextStyle, Tuple[float, float]]]:
    root = ET.fromstring(svg_text.encode("utf-8", errors="ignore"))
    vw, vh = _parse_viewbox(root)
    out: Dict[str, Tuple[SvgTextStyle, Tuple[float, float]]] = {}
    for el in root.iter():
        if _tag_name(el) != "text":
            continue
        raw = "".join(list(el.itertext()) or "").strip()
        if not raw:
            continue
        m = _TOKEN_RE.search(raw)
        if not m:
            continue
        token = m.group(1)
        x = _float_attr(el, "x", 0.0)
        y = _float_attr(el, "y", 0.0)
        font_size = _float_attr(el, "font-size", 16.0)
        font_family = _str_attr(el, "font-family", "Microsoft YaHei")
        fill = _str_attr(el, "fill", "#000000")
        anchor = _str_attr(el, "text-anchor", "start").lower()
        style = SvgTextStyle(
            x=x,
            y=y,
            font_size_px=max(1.0, float(font_size)),
            font_family=font_family,
            fill=fill,
            bold=_parse_bold(el),
            anchor=anchor,
        )
        out[token] = (style, (vw, vh))
    return out


def strip_svg_tokens(svg_text: str) -> str:
    return _TOKEN_RE.sub("", svg_text)


def render_svg_to_png_file(svg_text: str, *, out_dir: Path, out_prefix: str, width_px: int = 1920) -> Optional[str]:
    svg_norm = (svg_text or "").strip()
    if not svg_norm:
        return None
    try:
        root = ET.fromstring(svg_norm.encode("utf-8", errors="ignore"))
        vw, vh = _parse_viewbox(root)
    except Exception:
        vw, vh = 1280.0, 720.0
    width_px = max(640, int(width_px))
    height_px = max(360, int(round(float(width_px) * float(vh) / float(max(1.0, vw)))))
    key = hashlib.md5(f"{width_px}x{height_px}|{svg_norm}".encode("utf-8")).hexdigest()[:16]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = (out_dir / f"{out_prefix}_{key}.png").resolve()
    if out_path.exists() and out_path.is_file() and out_path.stat().st_size > 0:
        return str(out_path)

    png_bytes: Optional[bytes] = None
    try:
        try:
            import cairosvg  # type: ignore
        except Exception:
            vendor = (Path(__file__).resolve().parents[2] / "_vendor").resolve()
            if vendor.exists() and str(vendor) not in sys.path:
                sys.path.insert(0, str(vendor))
            import cairosvg  # type: ignore

        png_bytes = cairosvg.svg2png(bytestring=svg_norm.encode("utf-8"), output_width=width_px, output_height=height_px)
    except Exception:
        png_bytes = None

    if png_bytes is None:
        try:
            from svglib.svglib import svg2rlg  # type: ignore
            from reportlab.graphics import renderPM  # type: ignore

            drawing = svg2rlg(io.StringIO(svg_norm))
            png_bytes = renderPM.drawToString(drawing, fmt="PNG")
        except Exception:
            png_bytes = None

    if not png_bytes:
        return None

    out_path.write_bytes(png_bytes)
    return str(out_path)

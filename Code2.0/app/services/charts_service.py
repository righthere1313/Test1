from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Optional
import xml.etree.ElementTree as ET

from app.services.svg_render import render_svg_to_png_file


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _charts_root() -> Path:
    return _repo_root() / "charts"


def _assets_dir() -> Path:
    return Path("data/generated/ppt/assets").resolve()


def _tag_name(el: ET.Element) -> str:
    tag = el.tag or ""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _iter_text_elements(root: ET.Element):
    for el in root.iter():
        if _tag_name(el) == "text":
            yield el


def _get_text(el: ET.Element) -> str:
    return "".join(list(el.itertext()) or "").strip()


def _set_text(el: ET.Element, value: str) -> None:
    children = list(el)
    if children:
        for c in children:
            if _tag_name(c) == "tspan":
                c.text = value
                return
    el.text = value


def _float_attr(el: ET.Element, key: str, default: float = 0.0) -> float:
    raw = (el.get(key) or "").strip()
    if not raw:
        return default
    raw = raw.replace("px", "")
    try:
        return float(raw)
    except Exception:
        return default


def _nice_round_up(x: float) -> float:
    v = float(x)
    if v <= 0:
        return 1.0
    exp = math.floor(math.log10(v))
    base = 10 ** exp
    for m in [1, 2, 2.5, 5, 10]:
        if v <= m * base:
            return m * base
    return 10 * base


def _chart_file(chart_id: str) -> str:
    cid = (chart_id or "").strip()
    mapping = {
        "bar_chart": "bar_chart.svg",
        "line_chart": "line_chart.svg",
        "pie_chart": "pie_chart.svg",
    }
    if cid not in mapping:
        raise ValueError("unsupported chart id")
    return mapping[cid]


def _trim_list(xs: list[Any], limit: int, policy: str) -> list[Any]:
    if limit <= 0:
        return []
    if len(xs) <= limit:
        return xs
    pol = (policy or "trim").strip().lower()
    if pol != "trim":
        raise ValueError("chart data exceeds template capacity")
    return xs[:limit]


def _update_title_subtitle(root: ET.Element, title: Optional[str], subtitle: Optional[str]) -> None:
    if title:
        for el in _iter_text_elements(root):
            if abs(_float_attr(el, "y", 0.0) - 80.0) < 1.0 and _float_attr(el, "x", 0.0) <= 80.0:
                if "bold" in (el.get("font-weight") or "") or _float_attr(el, "font-size", 0.0) >= 28:
                    _set_text(el, str(title))
                    break
    if subtitle:
        for el in _iter_text_elements(root):
            if abs(_float_attr(el, "y", 0.0) - 115.0) < 2.0 and _float_attr(el, "x", 0.0) <= 80.0:
                if 14 <= _float_attr(el, "font-size", 0.0) <= 20:
                    _set_text(el, str(subtitle))
                    break


def _render_bar_chart(svg_text: str, data: dict, *, policy: str, title: Optional[str], subtitle: Optional[str]) -> str:
    root = ET.fromstring(svg_text.encode("utf-8", errors="ignore"))
    _update_title_subtitle(root, title, subtitle)
    chart_area = None
    for el in root.iter():
        if _tag_name(el) == "g" and (el.get("id") or "").strip() == "chartArea":
            chart_area = el
            break
    if chart_area is None:
        return svg_text

    categories = list(data.get("categories") or [])
    values = list(data.get("values") or [])
    n = min(len(categories), len(values))
    categories = [str(x) for x in categories[:n]]
    values_f = []
    for x in values[:n]:
        try:
            values_f.append(float(x))
        except Exception:
            values_f.append(0.0)

    categories = _trim_list(categories, 6, policy)
    values_f = _trim_list(values_f, 6, policy)
    n = min(len(categories), len(values_f))
    categories = categories[:n]
    values_f = values_f[:n]

    bars = []
    value_labels = []
    cat_labels = []
    y_axis_labels = []
    baseline_y = None
    top_y = None

    for el in chart_area:
        tag = _tag_name(el)
        if tag == "line":
            y1 = _float_attr(el, "y1", 0.0)
            y2 = _float_attr(el, "y2", 0.0)
            x1 = _float_attr(el, "x1", 0.0)
            x2 = _float_attr(el, "x2", 0.0)
            if abs(y1 - y2) < 0.01 and x2 > x1 and (baseline_y is None or y1 > baseline_y):
                baseline_y = y1
            if abs(y1 - y2) < 0.01 and x2 > x1 and (top_y is None or y1 < top_y):
                top_y = y1
        elif tag == "rect":
            w = _float_attr(el, "width", 0.0)
            h = _float_attr(el, "height", 0.0)
            if w > 10 and h > 10:
                bars.append(el)
        elif tag == "text":
            y = _float_attr(el, "y", 0.0)
            anchor = (el.get("text-anchor") or "").strip().lower()
            weight = (el.get("font-weight") or "").strip()
            if abs(y - 580.0) < 6.0 and anchor == "middle":
                cat_labels.append(el)
            elif anchor == "middle" and weight and float(y) < 560.0:
                value_labels.append(el)
            elif anchor == "end":
                y_axis_labels.append(el)

    if baseline_y is None:
        baseline_y = 550.0
    if top_y is None:
        top_y = 150.0

    bars.sort(key=lambda e: _float_attr(e, "x", 0.0))
    value_labels.sort(key=lambda e: _float_attr(e, "x", 0.0))
    cat_labels.sort(key=lambda e: _float_attr(e, "x", 0.0))

    if n <= 0 or not bars:
        return ET.tostring(root, encoding="unicode")

    max_val = max(values_f) if values_f else 1.0
    max_val = max(1e-6, float(max_val))
    span = float(baseline_y - top_y)

    for i in range(min(len(bars), n)):
        v = float(values_f[i])
        h = max(0.0, min(span, (v / max_val) * span))
        y = float(baseline_y) - h
        bars[i].set("y", f"{y:.2f}")
        bars[i].set("height", f"{h:.2f}")

    for i in range(min(len(value_labels), n)):
        _set_text(value_labels[i], f"{values_f[i]:g}")
        y = _float_attr(bars[i], "y", 0.0) - 14.0
        value_labels[i].set("y", f"{y:.2f}")

    for i in range(min(len(cat_labels), n)):
        _set_text(cat_labels[i], str(categories[i]))

    rounded = _nice_round_up(max_val)
    steps = 4
    vals = [int(round(rounded * (k / steps))) for k in range(0, steps + 1)]
    y_axis_labels.sort(key=lambda e: _float_attr(e, "y", 0.0), reverse=True)
    for i in range(min(len(y_axis_labels), len(vals))):
        _set_text(y_axis_labels[i], str(vals[i]))

    return ET.tostring(root, encoding="unicode")


def _render_line_chart(svg_text: str, data: dict, *, policy: str, title: Optional[str], subtitle: Optional[str]) -> str:
    root = ET.fromstring(svg_text.encode("utf-8", errors="ignore"))
    _update_title_subtitle(root, title, subtitle)
    chart_area = None
    for el in root.iter():
        if _tag_name(el) == "g" and (el.get("id") or "").strip() == "chartArea":
            chart_area = el
            break
    if chart_area is None:
        return svg_text

    x_labels = [str(x) for x in (data.get("x") or [])]
    series = list(data.get("series") or [])
    series = _trim_list(series, 2, policy)
    x_labels = _trim_list(x_labels, 12, policy)
    sx = []
    for s in series:
        if not isinstance(s, dict):
            continue
        name = str(s.get("name") or "").strip()
        vals = list(s.get("values") or [])
        vv = []
        for x in vals:
            try:
                vv.append(float(x))
            except Exception:
                vv.append(0.0)
        sx.append({"name": name, "values": _trim_list(vv, 12, policy)})

    n = min(len(x_labels), *(len(s["values"]) for s in sx)) if sx and x_labels else 0
    if n <= 0:
        return ET.tostring(root, encoding="unicode")
    x_labels = x_labels[:n]
    for s in sx:
        s["values"] = s["values"][:n]

    x_tick_texts = []
    polylines = []
    area_paths = []
    circles_by_color: dict[str, list[ET.Element]] = {}
    y_axis_labels = []
    baseline_y = None
    top_y = None

    for el in chart_area:
        tag = _tag_name(el)
        if tag == "line":
            y1 = _float_attr(el, "y1", 0.0)
            y2 = _float_attr(el, "y2", 0.0)
            x1 = _float_attr(el, "x1", 0.0)
            x2 = _float_attr(el, "x2", 0.0)
            if abs(y1 - y2) < 0.01 and x2 > x1 and (baseline_y is None or y1 > baseline_y):
                baseline_y = y1
            if abs(y1 - y2) < 0.01 and x2 > x1 and (top_y is None or y1 < top_y):
                top_y = y1
        elif tag == "text":
            y = _float_attr(el, "y", 0.0)
            anchor = (el.get("text-anchor") or "").strip().lower()
            if abs(y - 580.0) < 6.0 and anchor == "middle":
                x_tick_texts.append(el)
            elif anchor == "end":
                y_axis_labels.append(el)
        elif tag == "polyline":
            polylines.append(el)
        elif tag == "path":
            d = (el.get("d") or "").strip()
            if d.startswith("M "):
                area_paths.append(el)
        elif tag == "circle":
            fill = (el.get("fill") or "").strip()
            circles_by_color.setdefault(fill, []).append(el)

    if baseline_y is None:
        baseline_y = 550.0
    if top_y is None:
        top_y = 150.0

    x_tick_texts.sort(key=lambda e: _float_attr(e, "x", 0.0))
    for i in range(min(len(x_tick_texts), n)):
        _set_text(x_tick_texts[i], x_labels[i])

    xs = []
    if polylines:
        pts = (polylines[0].get("points") or "").strip().split()
        for p in pts:
            if "," not in p:
                continue
            x, _ = p.split(",", 1)
            try:
                xs.append(float(x))
            except Exception:
                pass
    xs = xs[:n] if xs else [225.0 + 85.0 * i for i in range(n)]

    all_vals = []
    for s in sx:
        all_vals.extend([float(v) for v in s["values"]])
    vmax = max(all_vals) if all_vals else 1.0
    vmax = max(1e-6, float(vmax))
    vnice = _nice_round_up(vmax)
    span = float(baseline_y - top_y)

    def y_of(v: float) -> float:
        return float(baseline_y) - (float(v) / vnice) * span

    area_paths.sort(key=lambda e: len((e.get("d") or "").strip()))
    polylines.sort(key=lambda e: len((e.get("points") or "").strip()))

    poly_targets = polylines[: len(sx)]
    area_targets = area_paths[: len(sx)]

    for si, s in enumerate(sx):
        ys = [y_of(v) for v in s["values"]]
        pts_str = " ".join([f"{xs[i]:g},{ys[i]:g}" for i in range(n)])
        if si < len(poly_targets):
            poly_targets[si].set("points", pts_str)
        if si < len(area_targets):
            d = "M " + " L ".join([f"{xs[i]:g},{ys[i]:g}" for i in range(n)])
            d += f" L {xs[-1]:g},{baseline_y:g} L {xs[0]:g},{baseline_y:g} Z"
            area_targets[si].set("d", d)

    color_keys = sorted(circles_by_color.keys())
    for si, s in enumerate(sx):
        fill = color_keys[si] if si < len(color_keys) else None
        circles = circles_by_color.get(fill, []) if fill else []
        circles.sort(key=lambda e: _float_attr(e, "cx", 0.0))
        ys = [y_of(v) for v in s["values"]]
        for i in range(min(len(circles), n)):
            circles[i].set("cy", f"{ys[i]:g}")

    steps = 5
    y_axis_labels.sort(key=lambda e: _float_attr(e, "y", 0.0), reverse=True)
    vals = [int(round(vnice * (k / steps))) for k in range(0, steps + 1)]
    for i in range(min(len(y_axis_labels), len(vals))):
        _set_text(y_axis_labels[i], str(vals[i]))

    return ET.tostring(root, encoding="unicode")


def _pie_wedge_path(r: float, a0: float, a1: float) -> str:
    x0 = r * math.cos(a0)
    y0 = r * math.sin(a0)
    x1 = r * math.cos(a1)
    y1 = r * math.sin(a1)
    large = 1 if (a1 - a0) % (2 * math.pi) > math.pi else 0
    return f"M 0,0 L {x0:.2f},{y0:.2f} A {r:.2f},{r:.2f} 0 {large},1 {x1:.2f},{y1:.2f} Z"


def _render_pie_chart(svg_text: str, data: dict, *, policy: str, title: Optional[str], subtitle: Optional[str]) -> str:
    root = ET.fromstring(svg_text.encode("utf-8", errors="ignore"))
    _update_title_subtitle(root, title, subtitle)
    items = list(data.get("items") or [])
    items = _trim_list(items, 5, policy)
    parsed = []
    for it in items:
        if not isinstance(it, dict):
            continue
        label = str(it.get("label") or "").strip() or "项"
        try:
            val = float(it.get("value") or 0.0)
        except Exception:
            val = 0.0
        parsed.append((label, max(0.0, val)))
    if not parsed:
        return ET.tostring(root, encoding="unicode")
    total = sum(v for _, v in parsed)
    if total <= 0:
        total = 1.0
    fracs = [v / total for _, v in parsed]

    pie_group = None
    for el in root.iter():
        if _tag_name(el) == "g" and (el.get("id") or "").strip() == "pieChart":
            pie_group = el
            break
    if pie_group is None:
        return ET.tostring(root, encoding="unicode")
    paths = [el for el in list(pie_group) if _tag_name(el) == "path"]
    for i in range(min(len(paths), len(fracs))):
        pass

    r = 200.0
    start = -math.pi / 2.0
    a = start
    for i in range(min(len(paths), len(fracs))):
        a_next = a + fracs[i] * 2.0 * math.pi
        paths[i].set("d", _pie_wedge_path(r, a, a_next))
        a = a_next

    pct_texts = []
    for el in root.iter():
        if _tag_name(el) != "text":
            continue
        t = _get_text(el)
        if t.endswith("%") and len(t) <= 4:
            pct_texts.append(el)
    pct_texts.sort(key=lambda e: _float_attr(e, "font-size", 0.0), reverse=True)
    pct_vals = [f"{int(round(fracs[i] * 100))}%" for i in range(len(fracs))]
    for i in range(min(len(pct_texts), len(pct_vals))):
        _set_text(pct_texts[i], pct_vals[i])

    legend_group = None
    for el in root.iter():
        if _tag_name(el) == "g" and (el.get("id") or "").strip() == "legend":
            legend_group = el
            break
    if legend_group is not None:
        legend_texts = [el for el in legend_group.iter() if _tag_name(el) == "text"]
        legend_texts.sort(key=lambda e: (_float_attr(e, "y", 0.0), _float_attr(e, "x", 0.0)))
        name_texts = [t for t in legend_texts if _float_attr(t, "x", 0.0) < 100]
        val_texts = [t for t in legend_texts if _float_attr(t, "x", 0.0) >= 200]
        for i in range(min(len(name_texts), len(parsed))):
            _set_text(name_texts[i], parsed[i][0])
        for i in range(min(len(val_texts), len(parsed))):
            pct = int(round(fracs[i] * 100))
            _set_text(val_texts[i], f"{parsed[i][1]:g} ({pct}%)")

    total_texts = []
    for el in root.iter():
        if _tag_name(el) != "text":
            continue
        if abs(_float_attr(el, "y", 0.0) - 270.0) < 2.0 and (_float_attr(el, "x", 0.0) > 400):
            total_texts.append(el)
    for el in total_texts[:1]:
        _set_text(el, f"{total:g} (100%)")

    return ET.tostring(root, encoding="unicode")


def render_chart_png(chart: dict, *, width_px: int = 1920) -> str:
    chart_id = str(chart.get("id") or "").strip()
    policy = str(chart.get("policy") or "trim").strip().lower()
    title = chart.get("title")
    subtitle = chart.get("subtitle")
    data = chart.get("data") if isinstance(chart.get("data"), dict) else {}
    svg_path = _charts_root() / _chart_file(chart_id)
    svg_text = svg_path.read_text(encoding="utf-8", errors="ignore")

    if chart_id == "bar_chart":
        rendered_svg = _render_bar_chart(svg_text, data, policy=policy, title=title, subtitle=subtitle)
    elif chart_id == "line_chart":
        rendered_svg = _render_line_chart(svg_text, data, policy=policy, title=title, subtitle=subtitle)
    elif chart_id == "pie_chart":
        rendered_svg = _render_pie_chart(svg_text, data, policy=policy, title=title, subtitle=subtitle)
    else:
        raise ValueError("unsupported chart id")

    key = hashlib.md5(json.dumps({"id": chart_id, "policy": policy, "title": title, "subtitle": subtitle, "data": data}, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    out_dir = _assets_dir()
    out = render_svg_to_png_file(rendered_svg, out_dir=out_dir, out_prefix=f"chart_{chart_id}_{key}", width_px=width_px)
    if not out:
        raise RuntimeError("chart render failed")
    return out


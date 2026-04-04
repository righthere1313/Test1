from __future__ import annotations

import re
from typing import Iterable, Optional


_BREAK_CHARS = set("，。；：、！？,.!?:;)]}）】》”’")


def max_chars_for_box(*, w_ratio: Optional[float], area_ratio: Optional[float], rank: Optional[int] = None) -> int:
    w = float(w_ratio) if isinstance(w_ratio, (int, float)) else 1.0
    a = float(area_ratio) if isinstance(area_ratio, (int, float)) else 1.0
    base = int(round(10 + 70 * max(0.0, min(1.0, w))))
    base = max(10, min(42, base))
    if a < 0.012:
        base = min(base, 22)
    if w < 0.18 or a < 0.008:
        base = min(base, 12)
    if rank == 1:
        base = max(base, 24)
    return int(base)


def _split_newlines(s: str) -> list[str]:
    if not s:
        return []
    parts = re.split(r"[\r\n]+", s)
    return [p.strip() for p in parts if p and p.strip()]


def _split_long_line(s: str, max_chars: int) -> list[str]:
    s = (s or "").strip()
    if not s:
        return []
    max_chars = max(1, int(max_chars))
    out: list[str] = []
    cur = s
    while len(cur) > max_chars:
        cut = max_chars
        lo = int(max_chars * 0.6)
        for i in range(max_chars - 1, lo - 1, -1):
            if cur[i] in _BREAK_CHARS:
                cut = i + 1
                break
        seg = cur[:cut].strip()
        if seg:
            out.append(seg)
        cur = cur[cut:].strip()
        if not cur:
            break
    if cur:
        out.append(cur)
    return out


def normalize_lines(lines: Iterable[str], *, max_chars: int) -> list[str]:
    out: list[str] = []
    for x in list(lines or []):
        s = str(x or "").strip()
        if not s:
            continue
        for part in _split_newlines(s):
            if len(part) <= max_chars:
                out.append(part)
            else:
                out.extend(_split_long_line(part, max_chars))
    return out


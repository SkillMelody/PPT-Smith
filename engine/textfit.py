"""Deterministic text measurement estimation.

P4 replaces the width model with real font metrics; the contract here is
stability: same text + same size -> same estimate, everywhere. The model
deliberately over-estimates a little (safety margin) so overflow is caught
at plan time, never discovered in the rendered deck.

Width model: CJK glyphs ~= 1.0 * size, Latin/digits ~= 0.55 * size,
spaces/punctuation ~= 0.35 * size. Line height comes from the style.
"""

from __future__ import annotations

import unicodedata

EMU_PER_PT = 12700


def _char_width_pt(char: str, size_pt: float) -> float:
    if unicodedata.east_asian_width(char) in ("W", "F"):
        return size_pt * 1.0
    if char.isspace() or unicodedata.category(char).startswith("P"):
        return size_pt * 0.38
    return size_pt * 0.56


def text_width_pt(text: str, size_cpt: int) -> float:
    size_pt = size_cpt / 100
    return sum(_char_width_pt(c, size_pt) for c in text)


def wrap_lines(text: str, size_cpt: int, width_emu: int) -> int:
    """Estimated wrapped line count for text in a box of width_emu."""
    if not text:
        return 0
    max_width_pt = max(width_emu / EMU_PER_PT, 1.0)
    lines, current = 1, 0.0
    for char in text:
        w = _char_width_pt(char, size_cpt / 100)
        if current + w > max_width_pt:
            lines += 1
            current = w
        else:
            current += w
    return lines


def text_height_emu(text: str, size_cpt: int, width_emu: int,
                    line_height_pct: int = 135) -> int:
    lines = max(wrap_lines(text, size_cpt, width_emu), 1)
    line_emu = int(size_cpt / 100 * line_height_pct / 100 * EMU_PER_PT)
    return lines * line_emu


def paragraphs_height_emu(paragraphs: list[dict], width_emu: int) -> int:
    """Estimated total height of render-plan paragraphs in a box.

    THE shared formula: layout fits with it, QA re-checks with it — one
    source of truth so the two can never disagree.
    """
    total = 0
    for para in paragraphs:
        text = "".join(r["text"] for r in para.get("runs", []))
        size = max((r["size_cpt"] for r in para.get("runs", [])), default=1200)
        total += text_height_emu(text, size, width_emu,
                                 para.get("line_height_pct", 135))
        total += int(para.get("space_after_cpt", 0) / 100 * EMU_PER_PT)
    return total


def fit_size_cpt(text: str, width_emu: int, height_emu: int,
                 levels_cpt: list[int], line_height_pct: int = 135) -> int | None:
    """Largest size level at which text fits the box; None if even the
    smallest overflows (caller must truncate — deterministically)."""
    for size in levels_cpt:
        if text_height_emu(text, size, width_emu, line_height_pct) <= height_emu:
            return size
    return None


def truncate_to_fit(text: str, size_cpt: int, width_emu: int, height_emu: int,
                    line_height_pct: int = 135) -> str:
    """Deterministic truncation rule (D9): cut at the last fitting char
    and close with an ellipsis."""
    if text_height_emu(text, size_cpt, width_emu, line_height_pct) <= height_emu:
        return text
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        candidate = text[:mid] + "…"
        if text_height_emu(candidate, size_cpt, width_emu, line_height_pct) <= height_emu:
            lo = mid
        else:
            hi = mid - 1
    return (text[:lo] + "…") if lo else "…"

from __future__ import annotations

import json
import os
from pathlib import Path

from engine.extractive_ir import build_extractive_ir
from engine.font_metrics import char_width_em, table_for
from engine.layout import layout_deck
from engine.policy import decide_deck
from engine.structural_parser import parse_markdown
from engine.style_pack import load_style_pack
from engine.textfit import text_width_pt, wrap_lines
from tests.unit.test_engine_p2 import MD

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "tests" / "fixtures" / "v4-golden" / "render-geometry.json"


# ---- font metrics -----------------------------------------------------------

def test_measured_table_differs_from_default_model():
    # Helvetica's measured 'i' is far narrower than the categorical default.
    assert char_width_em("i", "Helvetica") < 0.30
    assert char_width_em("i", "NoSuchFont") == 0.56


def test_cjk_width_clamped_to_full_width():
    # Helvetica.ttc reports a fallback advance for CJK; the renderer will
    # substitute a real CJK face at full width, so the clamp must hold.
    assert char_width_em("中", "Helvetica") >= 1.0
    assert char_width_em("中", "Songti SC") >= 1.0
    assert char_width_em("中") >= 1.0


def test_unknown_family_falls_back_to_default():
    assert table_for("Aptos")["family"] == "__default__"
    assert table_for("Helvetica")["family"] == "Helvetica"


def test_font_aware_width_changes_wrapping():
    text = "illiquidity minimum" * 6
    default_lines = wrap_lines(text, 1300, 2000000)
    helvetica_lines = wrap_lines(text, 1300, 2000000, "Helvetica")
    assert helvetica_lines <= default_lines
    assert text_width_pt("WWW", 1300, "Helvetica") > text_width_pt("iii", 1300, "Helvetica")


# ---- golden geometry regression --------------------------------------------

def _build_geometry() -> dict:
    doc = parse_markdown(MD, "src")
    ir = build_extractive_ir(doc, source_meta={"type": "markdown"})["ir"]
    style = load_style_pack()
    laid = layout_deck(ir, decide_deck(ir), style, {"src": doc})
    return {"canvas": laid["canvas"], "fonts_used": laid["fonts_used"],
            "slides": laid["slides"]}


def test_geometry_matches_committed_golden():
    """Same article x same style pack must reproduce the committed geometry
    byte-for-byte on every machine (D9). Intentional layout changes update
    the golden via REGEN_GOLDEN=1 python3 -m pytest tests/unit/test_engine_p4.py.
    """
    current = json.dumps(_build_geometry(), ensure_ascii=False, sort_keys=True,
                         indent=1)
    if os.environ.get("REGEN_GOLDEN") == "1" or not GOLDEN.exists():
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(current + "\n", encoding="utf-8")
    golden = GOLDEN.read_text(encoding="utf-8").rstrip("\n")
    assert current == golden, (
        "render geometry drifted from the committed golden; if the change "
        "is intentional, regenerate with REGEN_GOLDEN=1")

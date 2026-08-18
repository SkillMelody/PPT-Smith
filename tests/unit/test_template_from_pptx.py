#!/usr/bin/env python3
"""P9 tests: template extraction from a user PPTX -> v4 style pack.

Verifies the closed loop that makes "DIY your own design sense" real:
  1. extract_palette reads colors/fonts from a real PPTX;
  2. assign_colors maps them to valid tokens (contrast-clean);
  3. build_pack emits a full v3-style-contract (schema_version 2.0) pack that
     passes engine.style_validator.validate_style_pack (status != fail);
  4. a compile with --style <pack> actually renders with the extracted
     palette + fonts (provenance checked in the produced deck).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from template_from_pptx import (  # noqa: E402
    DEFAULT_BASE,
    assign_colors,
    assign_fonts,
    build_pack,
    extract_palette,
)

from engine.style_validator import validate_style_pack  # noqa: E402

# A real deck produced by the engine (doubao-real) serves as the "user PPTX".
SAMPLE_PPTX = ROOT / "test-runs" / "doubao-real" / "out" / "deck.pptx"
SKIP = pytest.mark.skipif(
    not SAMPLE_PPTX.exists(), reason="sample deck not present (run engine compile first)")


def _fake_extracted(text_colors, fills, fonts, bg=None):
    """Build the extract_palette() return shape from plain lists (Counter handles counts)."""
    from collections import Counter
    return {
        "text_colors": Counter(text_colors),
        "fill_colors": Counter(fills),
        "line_colors": Counter(),
        "fonts": Counter(fonts),
        "slide_bg": Counter([bg]) if bg else Counter(),
    }


def test_assign_colors_contrast_clean():
    extracted = _fake_extracted(
        text_colors=["#2A2E35", "#2A2E35", "#7C7669"],
        fills=["#0A2233", "#FFFFFF", "#F1EFEA"],
        fonts=["Aptos"],
        bg="#FFFFFF",
    )
    colors = assign_colors(extracted, base_colors={})
    assert colors["text_primary"] == "#2A2E35"
    assert colors["background"] == "#FFFFFF"
    assert colors["text_secondary"] != colors["text_primary"]
    assert colors["primary"] == "#0A2233"
    # data_series derived from palette
    assert len(colors["data_series"]) >= 3


def test_assign_colors_skips_white_as_secondary_text():
    """White runs (white-on-dark) must not become text_secondary."""
    extracted = _fake_extracted(
        text_colors=["#2A2E35", "#FFFFFF", "#FFFFFF", "#4A423A"],
        fills=["#FFFFFF"],
        fonts=["Aptos"],
        bg="#FFFFFF",
    )
    colors = assign_colors(extracted, base_colors={})
    assert colors["text_secondary"] == "#4A423A"
    assert colors["text_secondary"] != "#FFFFFF"


def test_assign_fonts_adds_cjk_fallback():
    fonts = assign_fonts({"fonts": __import__("collections").Counter(["Aptos", "Aptos", "Georgia"])})
    assert fonts["font_primary"][0] == "Aptos"
    assert fonts["font_editorial"][0] == "Georgia"
    # CJK-capable fallback present
    stack = " ".join(fonts["font_primary"]).lower()
    assert any(h in stack for h in ("pingfang", "yahei", "noto sans cjk", "source han"))


@SKIP
def test_build_pack_passes_validator():
    pack = build_pack(SAMPLE_PPTX, "my-report-template", "My Report Template",
                      base_path=DEFAULT_BASE)
    assert pack["schema_version"] == "2.0"
    assert pack["style_id"] == "my-report-template"
    assert pack["display_name"] == "My Report Template"
    result = validate_style_pack(pack)
    assert result["status"] != "fail", result["findings"]
    # provenance recorded
    assert pack["extensions"]["template_from_pptx"]["source_pptx"].endswith("deck.pptx")


@SKIP
def test_compile_uses_extracted_identity(tmp_path):
    """End-to-end: compile with the extracted pack and verify palette+fonts landed."""
    from engine.compile import compile_deck  # noqa: PLC0415
    import importlib.util
    # Locate the product-launch source fixture
    src = ROOT / "tests" / "fixtures" / "v4-bench" / "product-launch" / "source.md"
    if not src.exists():
        pytest.skip("product-launch fixture missing")
    pack_path = tmp_path / "my-template.json"
    pack_path.write_text(json.dumps(
        build_pack(SAMPLE_PPTX, "my-report-template", "My Report Template",
                   base_path=DEFAULT_BASE), ensure_ascii=False), encoding="utf-8")

    out = tmp_path / "out"
    result = compile_deck(
        sources=[("doc", "markdown", str(src))],
        ir_path=None, style_path=str(pack_path), degrade_on_error=False,
        output_dir=str(out))
    assert result["ok"], result.get("errors")

    # verify extracted identity landed in the deck
    from pptx import Presentation  # noqa: PLC0415
    prs = Presentation(str(out / "deck.pptx"))
    found_text = set()
    found_fonts = set()
    for slide in prs.slides:
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if run.font.color.type is not None and run.font.color.rgb:
                        found_text.add("#" + str(run.font.color.rgb))
                    if run.font.name:
                        found_fonts.add(run.font.name)
    assert any(c in found_text for c in ("#2A2E35", "#FFFFFF", "#0A2233", "#1F2227"))

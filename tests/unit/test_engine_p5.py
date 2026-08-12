from __future__ import annotations

import copy
import json
from pathlib import Path

from engine.extractive_ir import build_extractive_ir
from engine.layout import layout_deck
from engine.policy import decide_deck
from engine.structural_parser import parse_markdown
from engine.style_pack import load_style_pack
from engine.style_validator import validate_style_pack
from tests.unit.test_engine_p2 import MD

ROOT = Path(__file__).resolve().parents[2]
STYLE_DIR = ROOT / "styles"


def _load(pack_name: str) -> dict:
    return json.loads((STYLE_DIR / f"{pack_name}.json").read_text("utf-8"))


def test_all_builtin_packs_pass_authoring_qa():
    packs = sorted(STYLE_DIR.glob("*.json"))
    assert len(packs) >= 5
    for path in packs:
        result = validate_style_pack(json.loads(path.read_text("utf-8")))
        errors = [f for f in result["findings"] if f["severity"] == "error"]
        assert not errors, (path.name, errors)


def test_validator_rejects_low_contrast_palette():
    pack = _load("editorial-knowledge")
    pack["tokens"]["colors"]["text_primary"] = "#E9DFD0"  # ~= surface tones
    result = validate_style_pack(pack)
    assert result["status"] == "fail"
    assert any(f["code"].startswith("CONTRAST_TEXT_PRIMARY") for f in result["findings"])


def test_validator_warns_on_missing_cjk_stack():
    pack = _load("editorial-knowledge")
    pack["tokens"]["typography"]["font_primary"] = ["Helvetica", "Arial"]
    result = validate_style_pack(pack)
    assert any(f["code"] == "NO_CJK_FALLBACK" for f in result["findings"])


def test_validator_rejects_schema_violation():
    pack = _load("consulting-light")
    pack["grid"] = {"columns": 12}  # geometry is engine-owned
    result = validate_style_pack(pack)
    assert result["status"] == "fail"


def _topology(laid: dict) -> list:
    return [
        (slide["slide_id"],
         [(e["type"], e.get("semantic_role")) for e in slide["elements"]])
        for slide in laid["slides"]
    ]


def test_same_ir_multiple_styles_same_topology_different_tokens():
    """Acceptance metric 3 (plan §1.3): archetype selection and region
    topology are functions of the IR only; styles change tokens and
    bounded knob metrics, never structure."""
    doc = parse_markdown(MD, "src")
    ir = build_extractive_ir(doc, source_meta={"type": "markdown"})["ir"]
    decisions = decide_deck(ir)

    results = {}
    for name in ("editorial-knowledge", "consulting-light", "technical-blueprint"):
        style = load_style_pack(STYLE_DIR / f"{name}.json")
        results[name] = layout_deck(ir, copy.deepcopy(decisions), style, {"src": doc})

    topologies = {name: _topology(laid) for name, laid in results.items()}
    baseline = topologies["editorial-knowledge"]
    assert all(t == baseline for t in topologies.values()), "topology diverged by style"

    def title_color(laid):
        slide = laid["slides"][1]
        title = next(e for e in slide["elements"] if e.get("semantic_role") == "title")
        return title["paragraphs"][0]["runs"][0]["color"]

    colors = {name: title_color(laid) for name, laid in results.items()}
    assert len(set(colors.values())) >= 2, f"tokens did not take effect: {colors}"

    margins = {name: laid["slides"][1]["elements"][0]["frame"]["x"]
               for name, laid in results.items()}
    assert margins["editorial-knowledge"] != margins["technical-blueprint"], \
        "layout knobs (margin_scale) did not take effect"

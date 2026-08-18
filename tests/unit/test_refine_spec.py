"""P12-refine: compile-time refine spec (user chooses refinement at
generation time, per slide, still refineable afterwards).

Verifies:
  - compile --refine applies page-level intent by slide_id + block index
  - extractive IR (no block ids) is handled via index resolution
  - unknown slides / types / out-of-range indices are rejected honestly
    without failing the compile
  - refine spec wins over chart auto-inference
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.compile import compile_deck  # noqa: E402
from engine.refine_spec import apply_refine_spec, load_refine_spec  # noqa: E402

MD = """# 2025 年度经营总结

## 增长飞轮

- 内容生产提升 40%
- 渠道分发扩大 3 倍
- 用户留存提高 25%
- 收入增长 36%

## 对比

海外业务贡献 52%，国内贡献 8%。
"""


def _ir():
    return {
        "schema_version": "4.1.0",
        "deck": {"title": "2025 年度经营总结", "language": "zh"},
        "sources": [{"source_id": "src", "type": "markdown"}],
        "slides": [
            {"id": "s1", "title": "增长飞轮",
             "blocks": [{"role": "fact", "text": "增长飞轮"}]},
            {"id": "s2", "title": "区域对比",
             "blocks": [{"role": "metric", "label": "海外", "value": "52%"},
                        {"role": "metric", "label": "国内", "value": "8%"}]},
            {"id": "s3", "title": "拆解",
             "blocks": [{"role": "fact", "text": "驱动"},
                        {"role": "fact", "text": "海外 52%"},
                        {"role": "table"}]},
        ],
    }


class TestRefineSpecApplication:
    def test_apply_by_index(self):
        ir = _ir()
        report = apply_refine_spec(ir, {
            "s2": {"type": "contrast", "left": [0], "right": [1]},
        })
        assert report["applied"] == [{"slide_id": "s2", "type": "contrast"}]
        assert ir["slides"][1]["refine"]["type"] == "contrast"
        # blocks got auto-assigned ids for the slots
        left = ir["slides"][1]["refine"]["left"]
        right = ir["slides"][1]["refine"]["right"]
        assert left["blocks"] == ["b1"]
        assert right["blocks"] == ["b2"]

    def test_unknown_slide_rejected(self):
        ir = _ir()
        report = apply_refine_spec(ir, {"s99": {"type": "contrast"}})
        assert len(report["rejected"]) == 1
        assert report["rejected"][0]["code"] == "REFINE_SPEC_UNKNOWN_SLIDE"
        assert len(report["applied"]) == 0

    def test_unknown_type_rejected(self):
        ir = _ir()
        report = apply_refine_spec(ir, {"s2": {"type": "magic", "left": [0]}})
        assert report["rejected"][0]["code"] == "REFINE_SPEC_UNKNOWN_TYPE"

    def test_out_of_range_index_skipped(self):
        ir = _ir()
        report = apply_refine_spec(ir, {"s2": {"type": "contrast",
                                               "left": [0], "right": [99]}})
        assert report["applied"][0]["type"] == "contrast"
        # right slot resolves to empty (no crash)
        assert ir["slides"][1]["refine"]["right"]["blocks"] == []

    def test_split_with_visual(self):
        ir = _ir()
        apply_refine_spec(ir, {
            "s3": {"type": "split", "left": [0],
                   "right": [1, 2], "visual_right": {"chart": {"type": "column"}}},
        })
        refine = ir["slides"][2]["refine"]
        assert refine["type"] == "split"
        assert refine["right"]["visual"]["chart"]["type"] == "column"

    def test_load_spec(self, tmp_path):
        spec = tmp_path / "r.json"
        spec.write_text(json.dumps({"s1": {"type": "spotlight"}}))
        assert load_refine_spec(str(spec)) == {"s1": {"type": "spotlight"}}
        assert load_refine_spec(None) is None


class TestCompileWithRefineSpec:
    def test_compile_applies_spec(self, tmp_path):
        article = tmp_path / "a.md"
        article.write_text(MD, encoding="utf-8")
        spec = tmp_path / "r.json"
        spec.write_text(json.dumps({
            "s2": {"type": "contrast", "left": [0], "right": [1]},
        }), encoding="utf-8")
        report = compile_deck(
            sources=[("src", "markdown", str(article))],
            refine_spec_path=str(spec), output_dir=str(tmp_path / "out"))
        assert report["ok"], report
        assert report["refine_spec"]["applied"][0]["slide_id"] == "s2"
        # s2 rendered as contrast (has divider)
        plan = json.loads((tmp_path / "out" / "render-plan.json").read_text("utf-8"))
        s2 = plan["slides"][2]
        assert any(e.get("semantic_role") == "divider" for e in s2["elements"])
        # deck actually built
        assert (tmp_path / "out" / "deck.pptx").exists()

    def test_bad_spec_does_not_fail_compile(self, tmp_path):
        article = tmp_path / "a.md"
        article.write_text(MD, encoding="utf-8")
        spec = tmp_path / "r.json"
        spec.write_text(json.dumps({"s99": {"type": "contrast"}}),
                        encoding="utf-8")
        report = compile_deck(
            sources=[("src", "markdown", str(article))],
            refine_spec_path=str(spec), output_dir=str(tmp_path / "out"))
        assert report["ok"], "bad refine spec must not fail the compile"
        assert report["refine_spec"]["rejected"][0]["code"] == \
            "REFINE_SPEC_UNKNOWN_SLIDE"

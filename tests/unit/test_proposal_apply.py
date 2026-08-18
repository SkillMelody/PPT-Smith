"""P11 tests: L1/L2 autonomy proposal application, grid layout, hardening.

Verifies the autonomy tiers work end-to-end:
  - L1: model picks from engine candidate menu -> adopted or rejected honestly
  - L2: row/column grid proposal -> validated -> proposed_grid layout
  - rejected proposals fall back to the rule archetype (recorded, not failed)
  - local hardening flywheel: content-free pattern store + match + re-instantiate
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.autonomy import (  # noqa: E402
    harden,
    load_local_archetypes,
    match_local_archetype,
    rows_from_pattern,
    structure_of,
    validate_proposals,
)
from engine.compile import compile_deck  # noqa: E402
from engine.policy import decide_deck, decide_slide  # noqa: E402
from engine.proposal_apply import PROPOSED_GRID, apply_proposals  # noqa: E402

MD = """# 2025 年度经营总结

前言段落，介绍背景。

## 收入与增长

2025 年销售收入增长 36%，其中海外业务贡献最大。

- 海外业务收入 +52%
- 国内业务收入 +8%

| 区域 | 收入 | 同比 |
| --- | --- | --- |
| 海外 | 120 | +52% |
| 国内 | 300 | +8% |

## 风险

毛利率下降 2.8 个百分点。
"""


def _ir(with_proposal=None):
    slides = [{
        "id": "s1", "title": "增长由海外业务驱动",
        "blocks": [
            {"id": "b1", "role": "metric", "label": "总收入", "value": "+36%",
             "source_ref": {"source_id": "src", "loc": "para_2"}},
            {"id": "b2", "role": "metric", "label": "海外", "value": "+52%",
             "source_ref": {"source_id": "src", "loc": "list_1"}},
            {"id": "b3", "role": "risk", "text": "毛利率下降 2.8 个百分点"},
        ],
    }]
    if with_proposal:
        slides[0]["proposal"] = with_proposal
    return {
        "schema_version": "4.1.0",
        "deck": {"title": "2025 年度经营总结", "language": "zh"},
        "sources": [{"source_id": "src", "type": "markdown"}],
        "slides": slides,
    }


class TestL1Proposal:
    def test_valid_l1_choice_adopted(self):
        # kpi_wall is in the candidate menu (2 metric blocks).
        ir = _ir({"tier": "L1", "archetype_choice": "kpi_wall"})
        decisions = decide_deck(ir)
        report = apply_proposals(ir, decisions)
        assert len(report["accepted"]) == 1
        assert report["accepted"][0]["choice"] == "kpi_wall"
        d = decisions[0]
        assert d.chosen == "kpi_wall"
        assert d.chosen_by == "autonomy_l1"
        assert d.autonomy["tier"] == "L1"
        assert d.autonomy["proposal_accepted"] is True

    def test_invalid_l1_choice_rejected_with_fallback(self):
        ir = _ir({"tier": "L1", "archetype_choice": "quote_focus"})
        decisions = decide_deck(ir)
        report = apply_proposals(ir, decisions)
        assert len(report["rejected"]) == 1
        assert report["rejected"][0]["code"] == "PROPOSAL_L1_NOT_IN_MENU"
        d = decisions[0]
        # fell back to the rule choice
        assert d.chosen_by in ("rule", "fallback")
        assert d.autonomy["tier"] == "L0"
        assert d.autonomy["proposal_rejected"] is True

    def test_l1_missing_choice_rejected(self):
        ir = _ir({"tier": "L1"})
        decisions = decide_deck(ir)
        report = apply_proposals(ir, decisions)
        assert report["rejected"][0]["code"] == "PROPOSAL_L1_NO_CHOICE"


class TestL2Proposal:
    def test_valid_l2_grid_adopted(self):
        ir = _ir({"tier": "L2", "rows": [
            {"block_ids": ["b1", "b2"]}, {"block_ids": ["b3"]}]})
        decisions = decide_deck(ir)
        report = apply_proposals(ir, decisions)
        assert len(report["accepted"]) == 1
        assert report["accepted"][0]["tier"] == "L2"
        d = decisions[0]
        assert d.chosen == PROPOSED_GRID
        assert d.chosen_by == "autonomy_l2"
        assert d.autonomy["tier"] == "L2"

    def test_l2_duplicate_block_rejected(self):
        ir = _ir({"tier": "L2", "rows": [
            {"block_ids": ["b1", "b2"]}, {"block_ids": ["b1"]}]})
        decisions = decide_deck(ir)
        report = apply_proposals(ir, decisions)
        assert report["rejected"][0]["code"] == "PROPOSAL_DUPLICATE_BLOCK"
        d = decisions[0]
        assert d.autonomy["proposal_rejected"] is True
        assert d.chosen_by in ("rule", "fallback")

    def test_l2_unknown_block_rejected(self):
        ir = _ir({"tier": "L2", "rows": [{"block_ids": ["b1", "ghost"]}]})
        decisions = decide_deck(ir)
        report = apply_proposals(ir, decisions)
        assert report["rejected"][0]["code"] == "PROPOSAL_UNKNOWN_BLOCK"

    def test_validate_proposals_direct(self):
        errors = validate_proposals([{"slide_id": "s1", "rows": [
            {"block_ids": ["b1", "b2"]}]}],
            {"slides": [{"id": "s1", "blocks": [{"id": "b1"}, {"id": "b2"}]}]})
        assert errors == []


class TestLocalHardening:
    def test_harden_and_reinstantiate(self):
        proposal = {"rows": [{"block_ids": ["b1", "b2"]}, {"block_ids": ["b3"]}]}
        slide = {"blocks": [
            {"id": "b1", "role": "metric"}, {"id": "b2", "role": "metric"},
            {"id": "b3", "role": "table"}]}
        structure = structure_of(proposal, slide)
        assert structure["roles_signature"] == "metric:2|table:1"
        assert structure["rows"] == [{"roles": ["metric", "metric"]},
                                     {"roles": ["table"]}]
        with tempfile.TemporaryDirectory() as td:
            store = Path(td)
            record = harden(proposal, slide, store=store)
            assert record["pattern_id"].startswith("local-")
            records = load_local_archetypes(store)
            assert len(records) == 1
            # new isomorphic slide matches and re-instantiates
            new_slide = {"blocks": [
                {"id": "x1", "role": "metric"}, {"id": "x2", "role": "metric"},
                {"id": "x3", "role": "table"}]}
            match = match_local_archetype(new_slide, records)
            assert match is not None
            rows = rows_from_pattern(new_slide, match)
            assert rows == [{"block_indices": [0, 1]}, {"block_indices": [2]}]

    def test_no_match_for_different_signature(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td)
            harden({"rows": [{"block_ids": ["b1", "b2"]}, {"block_ids": ["b3"]}]},
                   {"blocks": [{"id": "b1", "role": "metric"},
                               {"id": "b2", "role": "metric"},
                               {"id": "b3", "role": "table"}]},
                   store=store)
            records = load_local_archetypes(store)
            other = {"blocks": [{"id": "a", "role": "fact"}]}
            assert match_local_archetype(other, records) is None


class TestEndToEnd:
    def test_compile_with_l2_grid(self, tmp_path):
        """Full compile: IR with L2 proposal -> proposed_grid archetype -> deck."""
        article = tmp_path / "article.md"
        article.write_text(MD, encoding="utf-8")
        ir_path = tmp_path / "ir.json"
        ir = {
            "schema_version": "4.1.0",
            "deck": {"title": "2025 年度经营总结", "language": "zh"},
            "sources": [{"source_id": "src", "type": "markdown"}],
            "slides": [{
                "id": "s2", "title": "分区域明细",
                "proposal": {"tier": "L2", "rows": [
                    {"block_ids": ["b1", "b2"]}, {"block_ids": ["b3"]}]},
                "blocks": [
                    {"id": "b1", "role": "metric", "label": "海外", "value": "120",
                     "source_ref": {"source_id": "src", "loc": "table_1"}},
                    {"id": "b2", "role": "metric", "label": "国内", "value": "300",
                     "source_ref": {"source_id": "src", "loc": "table_1"}},
                    {"id": "b3", "role": "table",
                     "source_ref": {"source_id": "src", "loc": "table_1"}},
                ],
            }],
        }
        ir_path.write_text(json.dumps(ir, ensure_ascii=False), encoding="utf-8")
        report = compile_deck(
            sources=[("src", "markdown", str(article))],
            ir_path=str(ir_path), output_dir=str(tmp_path / "out"))
        assert report["ok"], report
        assert report["ir_origin"] == "provided"
        assert report["qa"]["error_count"] == 0
        trace = json.loads((tmp_path / "out" / "decision-trace.json").read_text("utf-8"))
        assert trace["decisions"][0]["chosen"] == PROPOSED_GRID
        assert trace["decisions"][0]["chosen_by"] == "autonomy_l2"
        assert trace["decisions"][0]["autonomy"]["tier"] == "L2"

    def test_compile_with_rejected_l1(self, tmp_path):
        """Rejected proposal: compiles fine, archetype falls back, trace honest."""
        article = tmp_path / "article.md"
        article.write_text(MD, encoding="utf-8")
        ir_path = tmp_path / "ir.json"
        ir = _ir({"tier": "L1", "archetype_choice": "quote_focus"})
        ir["sources"] = [{"source_id": "src", "type": "markdown"}]
        ir_path.write_text(json.dumps(ir, ensure_ascii=False), encoding="utf-8")
        report = compile_deck(
            sources=[("src", "markdown", str(article))],
            ir_path=str(ir_path), output_dir=str(tmp_path / "out"))
        assert report["ok"], report
        assert report["autonomy"]["rejected"][0]["code"] == "PROPOSAL_L1_NOT_IN_MENU"
        trace = json.loads((tmp_path / "out" / "decision-trace.json").read_text("utf-8"))
        assert trace["decisions"][0]["autonomy"]["proposal_rejected"] is True

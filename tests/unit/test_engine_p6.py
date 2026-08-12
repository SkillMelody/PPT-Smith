"""P6 tests — Autonomy tiers (D7/D10).

Covers grade_probe, validate_proposals, harden/load_local_archetypes,
rows_from_pattern, match_local_archetype, and contribution_bundle.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from engine.autonomy import (
    contribution_bundle,
    grade_probe,
    harden,
    load_local_archetypes,
    match_local_archetype,
    rows_from_pattern,
    structure_of,
    validate_proposals,
)

# ---------------------------------------------------------------------------
# Minimal IR fixtures
# ---------------------------------------------------------------------------

MINIMAL_IR = {
    "slides": [
        {
            "id": "s1",
            "message": "Revenue grew 24 %.",
            "blocks": [
                {"id": "b1", "role": "metric", "text": "1.2亿元"},
                {"id": "b2", "role": "body", "text": "订阅收入 +31%"},
            ],
            "relations": [{"from": "b1", "to": "b2", "type": "supports"}],
        }
    ]
}

BARE_IR = {
    "slides": [
        {
            "id": "s1",
            "blocks": [{"id": "b1", "role": "body", "text": "plain text"}],
        }
    ]
}


# ---------------------------------------------------------------------------
# grade_probe
# ---------------------------------------------------------------------------

class TestGradeProbe:
    def test_schema_error_forces_l0(self):
        result = grade_probe(MINIMAL_IR, schema_errors=["err"], provenance_errors=[])
        assert result["tier"] == "L0"
        assert result["probe"]["result"] == "fail"

    def test_provenance_error_forces_l0(self):
        result = grade_probe(MINIMAL_IR, schema_errors=[], provenance_errors=["e"])
        assert result["tier"] == "L0"

    def test_enriched_ir_grants_l2(self):
        result = grade_probe(MINIMAL_IR, schema_errors=[], provenance_errors=[])
        assert result["tier"] == "L2"
        assert result["probe"]["result"] == "pass"
        assert result["probe"]["ir_roundtrip_valid"] is True

    def test_bare_ir_grants_l1(self):
        result = grade_probe(BARE_IR, schema_errors=[], provenance_errors=[])
        assert result["tier"] == "L1"
        assert result["probe"]["result"] == "pass"

    def test_empty_ir_grants_l1(self):
        result = grade_probe({}, schema_errors=[], provenance_errors=[])
        assert result["tier"] == "L1"

    def test_result_keys_present(self):
        result = grade_probe(MINIMAL_IR, schema_errors=[], provenance_errors=[])
        assert {"tier", "probe", "reason", "schema_error_count",
                "provenance_error_count"} <= result.keys()


# ---------------------------------------------------------------------------
# validate_proposals
# ---------------------------------------------------------------------------

class TestValidateProposals:
    def _proposal(self, **overrides):
        p = {
            "slide_id": "s1",
            "rows": [{"block_ids": ["b1"]}, {"block_ids": ["b2"]}],
        }
        p.update(overrides)
        return p

    def test_valid_proposal_no_errors(self):
        errors = validate_proposals([self._proposal()], MINIMAL_IR)
        assert errors == []

    def test_unknown_slide(self):
        errors = validate_proposals(
            [self._proposal(slide_id="s_unknown")], MINIMAL_IR)
        codes = [e["code"] for e in errors]
        assert "PROPOSAL_UNKNOWN_SLIDE" in codes

    def test_too_many_rows(self):
        rows = [{"block_ids": ["b1"]}] * 7  # MAX_ROWS = 6
        errors = validate_proposals([self._proposal(rows=rows)], MINIMAL_IR)
        codes = [e["code"] for e in errors]
        assert "PROPOSAL_ROWS_OUT_OF_RANGE" in codes

    def test_empty_rows(self):
        errors = validate_proposals([self._proposal(rows=[])], MINIMAL_IR)
        codes = [e["code"] for e in errors]
        assert "PROPOSAL_ROWS_OUT_OF_RANGE" in codes

    def test_too_many_cols(self):
        rows = [{"block_ids": ["b1", "b2", "b1", "b2", "b1"]}]  # MAX_COLS = 4
        errors = validate_proposals([self._proposal(rows=rows)], MINIMAL_IR)
        codes = [e["code"] for e in errors]
        assert "PROPOSAL_COLS_OUT_OF_RANGE" in codes

    def test_unknown_block(self):
        rows = [{"block_ids": ["b999"]}]
        errors = validate_proposals([self._proposal(rows=rows)], MINIMAL_IR)
        codes = [e["code"] for e in errors]
        assert "PROPOSAL_UNKNOWN_BLOCK" in codes

    def test_duplicate_block(self):
        rows = [{"block_ids": ["b1"]}, {"block_ids": ["b1"]}]
        errors = validate_proposals([self._proposal(rows=rows)], MINIMAL_IR)
        codes = [e["code"] for e in errors]
        assert "PROPOSAL_DUPLICATE_BLOCK" in codes

    def test_multiple_proposals(self):
        good = self._proposal()
        bad = self._proposal(slide_id="s_nope")
        errors = validate_proposals([good, bad], MINIMAL_IR)
        assert len(errors) == 1
        assert "/proposals/1" in errors[0]["path"]


# ---------------------------------------------------------------------------
# harden / load_local_archetypes / match_local_archetype / rows_from_pattern
# ---------------------------------------------------------------------------

class TestHardenAndLoad:
    def test_harden_creates_file(self, tmp_path):
        proposal = {"rows": [{"block_ids": ["b1"]}, {"block_ids": ["b2"]}]}
        slide = MINIMAL_IR["slides"][0]
        record = harden(proposal, slide, store=tmp_path)
        assert record["pattern_id"].startswith("local-")
        assert (tmp_path / f"{record['pattern_id']}.json").exists()

    def test_harden_is_content_free(self, tmp_path):
        proposal = {"rows": [{"block_ids": ["b1"]}, {"block_ids": ["b2"]}]}
        slide = MINIMAL_IR["slides"][0]
        record = harden(proposal, slide, store=tmp_path)
        raw = json.dumps(record)
        # No source text must leak into the hardened record
        assert "1.2亿元" not in raw
        assert "订阅收入" not in raw

    def test_harden_records_role_structure(self, tmp_path):
        proposal = {"rows": [{"block_ids": ["b1"]}, {"block_ids": ["b2"]}]}
        slide = MINIMAL_IR["slides"][0]
        record = harden(proposal, slide, store=tmp_path)
        assert record["rows"][0]["roles"] == ["metric"]
        assert record["rows"][1]["roles"] == ["body"]

    def test_load_returns_hardened_records(self, tmp_path):
        proposal = {"rows": [{"block_ids": ["b1"]}]}
        slide = MINIMAL_IR["slides"][0]
        harden(proposal, slide, store=tmp_path)
        records = load_local_archetypes(store=tmp_path)
        assert len(records) == 1
        assert records[0]["pattern_id"].startswith("local-")

    def test_load_empty_store(self, tmp_path):
        records = load_local_archetypes(store=tmp_path)
        assert records == []

    def test_load_skips_corrupt_file(self, tmp_path):
        (tmp_path / "local-badfile.json").write_text("not json", encoding="utf-8")
        records = load_local_archetypes(store=tmp_path)
        assert records == []

    def test_match_finds_by_signature(self, tmp_path):
        proposal = {"rows": [{"block_ids": ["b1"]}, {"block_ids": ["b2"]}]}
        slide = MINIMAL_IR["slides"][0]
        record = harden(proposal, slide, store=tmp_path)
        records = load_local_archetypes(store=tmp_path)
        matched = match_local_archetype(slide, records)
        assert matched is not None
        assert matched["pattern_id"] == record["pattern_id"]

    def test_match_returns_none_on_mismatch(self, tmp_path):
        proposal = {"rows": [{"block_ids": ["b1"]}]}
        slide = MINIMAL_IR["slides"][0]
        harden(proposal, slide, store=tmp_path)
        records = load_local_archetypes(store=tmp_path)
        other_slide = {
            "id": "s2",
            "blocks": [{"id": "x1", "role": "title"}, {"id": "x2", "role": "title"}],
        }
        assert match_local_archetype(other_slide, records) is None

    def test_rows_from_pattern_instantiates(self, tmp_path):
        proposal = {"rows": [{"block_ids": ["b1"]}, {"block_ids": ["b2"]}]}
        slide = MINIMAL_IR["slides"][0]
        record = harden(proposal, slide, store=tmp_path)
        rows = rows_from_pattern(slide, record)
        assert rows is not None
        assert len(rows) == 2

    def test_rows_from_pattern_returns_none_on_role_exhaustion(self, tmp_path):
        # record expects 2 "metric" rows but slide only has 1 metric block
        record = {
            "pattern_id": "local-test",
            "version": 1,
            "roles_signature": "metric:1|body:1",
            "rows": [
                {"roles": ["metric"]},
                {"roles": ["metric"]},  # exhausts the single metric block
            ],
        }
        slide = MINIMAL_IR["slides"][0]
        rows = rows_from_pattern(slide, record)
        assert rows is None


# ---------------------------------------------------------------------------
# contribution_bundle
# ---------------------------------------------------------------------------

class TestContributionBundle:
    def _trace(self):
        return {
            "decisions": [
                {
                    "stage": "archetype",
                    "evidence": {"metric_count": 1},
                    "candidates": ["kpi_wall", "evidence_stack"],
                    "chosen": "kpi_wall",
                    "chosen_by": "rule",
                    "confidence": 0.9,
                }
            ]
        }

    def test_bundle_structure(self, tmp_path):
        bundle = contribution_bundle([self._trace()], store=tmp_path)
        assert bundle["bundle_version"] == 1
        assert "local_archetypes" in bundle
        assert "decisions" in bundle

    def test_bundle_decisions_content_free(self, tmp_path):
        bundle = contribution_bundle([self._trace()], store=tmp_path)
        raw = json.dumps(bundle)
        # Symbolic features only — no prose from any source
        assert "订阅收入" not in raw

    def test_bundle_includes_hardened_archetypes(self, tmp_path):
        proposal = {"rows": [{"block_ids": ["b1"]}]}
        slide = MINIMAL_IR["slides"][0]
        harden(proposal, slide, store=tmp_path)
        bundle = contribution_bundle([], store=tmp_path)
        assert len(bundle["local_archetypes"]) == 1

    def test_bundle_empty_traces(self, tmp_path):
        bundle = contribution_bundle([], store=tmp_path)
        assert bundle["decisions"] == []

    def test_bundle_flattens_multiple_traces(self, tmp_path):
        bundle = contribution_bundle([self._trace(), self._trace()], store=tmp_path)
        assert len(bundle["decisions"]) == 2

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from engine.design_contract import validate_design_contract


def _evidence() -> dict:
    return {
        "schema_version": "1.0.0", "status": "unreviewed",
        "source": {"filename": "reference.pptx", "sha256": "sha256:" + "a" * 64,
                   "slide_count": 2, "slide_size_in": {"width": 13.333, "height": 7.5}},
        "tokens": {"colors": [], "fonts": [], "font_sizes_pt": []},
        "slides": [
            {"slide_index": 1, "object_count": 20, "density": "medium", "occupied_area_sum": 0.4,
             "geometry": {"text": 8, "shape": 12}, "title_candidates": [], "elements": []},
            {"slide_index": 2, "object_count": 28, "density": "high", "occupied_area_sum": 0.6,
             "geometry": {"text": 12, "shape": 16}, "title_candidates": [], "elements": []},
        ],
        "rhythm": {"density_sequence": ["medium", "high"], "object_count_sequence": [20, 28]},
        "review": {"required": True, "state": "unreviewed"},
        "limitations": ["Evidence only."],
    }


def _ir() -> dict:
    return {
        "schema_version": "4.1.0",
        "deck": {"title": "Q3 growth review", "language": "en-US"},
        "sources": [{"source_id": "doc", "type": "markdown", "path": "source.md"}],
        "slides": [{
            "id": "growth", "title": "Growth accelerated", "message": "Growth accelerated in Q3.",
            "blocks": [
                {"id": "m_growth", "role": "metric", "label": "Q3 growth", "value": "24%",
                 "source_ref": {"source_id": "doc", "loc": "para_1"}},
                {"id": "f_driver", "role": "fact", "text": "New products drove the majority of growth.",
                 "source_ref": {"source_id": "doc", "loc": "para_1"}},
            ],
            "chart": {"type": "bar", "source_ref": {"source_id": "doc", "loc": "table_1"},
                      "data": {"categories": ["Q2", "Q3"], "series": [{"name": "Growth", "values": [12, 24]}]}},
        }],
    }


def _contract() -> dict:
    return {
        "schema_version": "1.0.0",
        "contract_id": "q3-growth-template-slice",
        "status": "draft",
        "source_ir_sha256": "sha256:" + hashlib.sha256(
            json.dumps(_ir(), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "template_evidence": {"source_sha256": "sha256:" + "a" * 64, "slide_indices": [2]},
        "pages": [{
            "slide_id": "growth",
            "template_slide_index": 2,
            "composition": "metric_proof",
            "message_ref": {"kind": "slide_message"},
            "primary_ref": {"kind": "block", "block_id": "m_growth"},
            "evidence_refs": [{"kind": "block", "block_id": "f_driver"}],
            "visual_ref": {"kind": "chart"},
        }],
        "review": {"state": "unreviewed", "evidence": []},
    }


def test_design_contract_accepts_only_ir_references() -> None:
    assert validate_design_contract(_contract(), _ir(), _evidence()) == []


def test_design_contract_rejects_unknown_block_reference() -> None:
    contract = _contract()
    contract["pages"][0]["primary_ref"]["block_id"] = "invented_metric"
    findings = validate_design_contract(contract, _ir(), _evidence())
    assert any(item["code"] == "CONTRACT_BLOCK_REF_UNKNOWN" for item in findings)


def test_design_contract_rejects_source_ir_hash_mismatch() -> None:
    contract = _contract()
    contract["source_ir_sha256"] = "sha256:" + "c" * 64
    findings = validate_design_contract(contract, _ir(), _evidence())
    assert any(item["code"] == "CONTRACT_IR_HASH_MISMATCH" for item in findings)


def test_design_contract_rejects_template_hash_mismatch() -> None:
    contract = _contract()
    contract["template_evidence"]["source_sha256"] = "sha256:" + "c" * 64
    findings = validate_design_contract(contract, _ir(), _evidence())
    assert any(item["code"] == "CONTRACT_TEMPLATE_HASH_MISMATCH" for item in findings)


def test_design_contract_draft_cannot_claim_approved_review() -> None:
    contract = _contract()
    contract["review"]["state"] = "approved"
    findings = validate_design_contract(contract, _ir(), _evidence())
    assert any(item["code"] == "CONTRACT_REVIEW_STATE_INVALID" for item in findings)


def test_action_roadmap_requires_source_bound_steps() -> None:
    contract = _contract()
    contract["pages"][0]["composition"] = "action_roadmap"
    findings = validate_design_contract(contract, _ir(), _evidence())
    assert any(item["code"] == "CONTRACT_COMPOSITION_CONTENT_MISMATCH" for item in findings)


def test_design_contract_has_no_free_text_fields_in_page_spec() -> None:
    contract = _contract()
    contract["pages"][0]["invented_caption"] = "High performers lead transformation"
    findings = validate_design_contract(contract, _ir(), _evidence())
    assert any(item["code"] == "SCHEMA" for item in findings)

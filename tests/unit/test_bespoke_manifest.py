from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from engine.bespoke import build_authoring_manifest

ROOT = Path(__file__).resolve().parents[2]


def _ir(*, slides: int = 2) -> dict:
    return {
        "schema_version": "4.1.0",
        "deck": {"title": "Long-form management review", "language": "en-US"},
        "sources": [{"source_id": "doc", "type": "markdown", "path": "source.md"}],
        "slides": [
            {
                "id": f"s{index + 1}",
                "title": f"Decision message {index + 1}",
                "message": f"Evidence supports decision {index + 1}.",
                "blocks": [{
                    "id": f"f{index + 1}", "role": "fact",
                    "text": f"Source-bound fact {index + 1}.",
                    "source_ref": {"source_id": "doc", "loc": f"para_{index + 1}"},
                }],
            }
            for index in range(slides)
        ],
    }


def _request(*, pages: int = 2, delivery_scope: str | None = None) -> dict:
    request = {
        "schema_version": "1.0.0",
        "request_id": "long-form-management-review",
        "route": "bespoke",
        "page_contract": {
            "mode": "exact", "exact_pages": pages,
            "overflow_policy": "ask", "underflow_policy": "fewer_pages",
        },
    }
    if delivery_scope is not None:
        request["delivery_scope"] = delivery_scope
    return request


def _assessment(*, minimum: int = 2, recommended: int = 2, maximum: int = 3) -> dict:
    return {
        "minimum_viable_pages": minimum,
        "recommended_pages": recommended,
        "maximum_useful_pages": maximum,
        "basis": ["two mandatory decision messages"],
    }


def _sha(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _narrative_contract(ir: dict) -> dict:
    return {
        "schema_version": "1.0.0",
        "contract_id": "management-review-narrative",
        "source_ir_sha256": _sha(ir),
        "quality_principles": [
            "audience_decision_alignment",
            "assertion_evidence",
            "coherence_progression",
            "cognitive_load",
            "semantic_visual_encoding",
        ],
        "freedom": {
            "model_owns": [
                "storyline", "page_composition", "visual_encoding",
                "geometry", "cross_page_rhythm",
            ],
            "engine_verifies": [
                "source_fidelity", "page_contract", "native_editability",
                "render_integrity", "visual_review",
            ],
            "forbidden_prescriptions": [
                "composition_enum", "coordinate_grid",
                "template_slide_mapping", "archetype_selection",
            ],
        },
        "deck": {
            "audience_decision": "Choose how to scale AI beyond pilots.",
            "core_thesis": "Workflow redesign and leadership ownership separate high performers.",
            "narrative_arc": "Expose the scale gap, explain the operating differences, close with action.",
        },
        "chapters": [{
            "chapter_id": "ch1",
            "title": "From adoption to scale",
            "job": "Convert evidence into a management decision.",
            "slide_ids": ["s1", "s2"],
        }],
        "pages": [
            {
                "slide_id": "s1",
                "audience_question": "Why has adoption not produced enterprise value?",
                "assertion_ref": "slide:s1:message",
                "evidence_refs": ["block:s1:f1"],
                "narrative_function": "establish_tension",
                "transition_to_next": "Move from the value gap to the operating difference.",
            },
            {
                "slide_id": "s2",
                "audience_question": "What should leaders change first?",
                "assertion_ref": "slide:s2:message",
                "evidence_refs": ["block:s2:f2"],
                "narrative_function": "resolve_with_action",
                "transition_to_next": None,
            },
        ],
    }


def test_bespoke_manifest_gives_design_rights_to_model_and_verification_to_engine() -> None:
    ir = _ir()

    manifest = build_authoring_manifest(_request(), ir, _assessment())

    assert manifest["status"] == "ready_for_authoring"
    assert manifest["route"] == "bespoke"
    assert manifest["source_ir_sha256"] == _sha(ir)
    assert manifest["page_budget"]["planned_pages"] == 2
    assert manifest["ownership"] == {
        "narrative": "high_capability_model",
        "visual_design": "high_capability_model",
        "geometry": "high_capability_model",
        "verification": "ppt_smith_engine",
    }
    assert manifest["requires_standard_base_deck"] is False
    assert "base_deck" not in manifest
    assert "composition" not in json.dumps(manifest)


def test_bespoke_manifest_exposes_source_bound_page_content_without_layout_enum() -> None:
    manifest = build_authoring_manifest(_request(), _ir(), _assessment())

    first = manifest["pages"][0]
    assert first["slide_id"] == "s1"
    assert first["required_bindings"] == [
        "slide:s1:title", "slide:s1:message", "block:s1:f1:text",
    ]
    assert first["layout_freedom"] == "unrestricted_within_delivery_gates"
    assert "template_slide_index" not in first


def test_bespoke_manifest_rejects_storyboard_count_that_does_not_match_page_budget() -> None:
    manifest = build_authoring_manifest(_request(pages=3), _ir(slides=2), _assessment(maximum=4))

    assert manifest["status"] == "rejected"
    assert manifest["code"] == "STORYBOARD_PAGE_COUNT_MISMATCH"
    assert manifest["planned_pages"] == 3
    assert manifest["ir_slide_count"] == 2


def test_bespoke_manifest_propagates_page_contract_conflict() -> None:
    manifest = build_authoring_manifest(
        _request(pages=1), _ir(slides=2),
        _assessment(minimum=2, recommended=2, maximum=4),
    )

    assert manifest["status"] == "page_contract_conflict"
    assert manifest["page_budget"]["code"] == "PAGE_CONTRACT_CONTENT_OVERFLOW"
    assert "pages" not in manifest


def test_complete_deck_requires_a_professional_narrative_contract() -> None:
    manifest = build_authoring_manifest(
        _request(delivery_scope="complete_deck"), _ir(), _assessment(),
    )

    assert manifest["status"] == "rejected"
    assert manifest["code"] == "NARRATIVE_CONTRACT_REQUIRED"


def test_complete_deck_locks_professional_narrative_quality_without_layout_prescriptions() -> None:
    ir = _ir()
    contract = _narrative_contract(ir)

    manifest = build_authoring_manifest(
        _request(delivery_scope="complete_deck"), ir, _assessment(),
        narrative_contract=contract,
    )

    assert manifest["status"] == "ready_for_authoring"
    assert manifest["delivery_scope"] == "complete_deck"
    assert manifest["narrative_contract"] == {**contract, "sha256": _sha(contract)}
    assert all(
        not ({"composition", "layout", "page_archetype", "template_slide_index"} & set(page))
        for page in manifest["narrative_contract"]["pages"]
    )


def test_narrative_contract_rejects_prescriptive_design_fields() -> None:
    ir = _ir()
    contract = _narrative_contract(ir)
    contract["pages"][0]["composition"] = "metric_proof"

    manifest = build_authoring_manifest(
        _request(delivery_scope="complete_deck"), ir, _assessment(),
        narrative_contract=contract,
    )

    assert manifest["status"] == "rejected"
    assert manifest["code"] == "NARRATIVE_CONTRACT_INVALID"
    assert any(
        finding["code"] == "NARRATIVE_PRESCRIPTIVE_FIELD"
        and finding["path"] == "/pages/0/composition"
        for finding in manifest["findings"]
    )


def test_narrative_contract_must_bind_the_exact_source_ir() -> None:
    ir = _ir()
    contract = _narrative_contract(ir)
    contract["source_ir_sha256"] = "sha256:" + "0" * 64

    manifest = build_authoring_manifest(
        _request(delivery_scope="complete_deck"), ir, _assessment(),
        narrative_contract=contract,
    )

    assert manifest["status"] == "rejected"
    assert manifest["code"] == "NARRATIVE_CONTRACT_INVALID"
    assert any(
        finding["code"] == "NARRATIVE_SOURCE_IR_MISMATCH"
        for finding in manifest["findings"]
    )


def test_narrative_contract_requires_the_professional_quality_principles() -> None:
    ir = _ir()
    contract = _narrative_contract(ir)
    contract.pop("quality_principles")

    manifest = build_authoring_manifest(
        _request(delivery_scope="complete_deck"), ir, _assessment(),
        narrative_contract=contract,
    )

    assert manifest["status"] == "rejected"
    assert any(
        finding["code"] == "NARRATIVE_SCHEMA"
        and finding["path"] == "/quality_principles"
        for finding in manifest["findings"]
    )


def test_narrative_chapters_must_partition_ir_slides_in_story_order() -> None:
    ir = _ir()
    contract = _narrative_contract(ir)
    contract["chapters"][0]["slide_ids"] = ["s2", "s1"]

    manifest = build_authoring_manifest(
        _request(delivery_scope="complete_deck"), ir, _assessment(),
        narrative_contract=contract,
    )

    assert manifest["status"] == "rejected"
    assert any(
        finding["code"] == "NARRATIVE_CHAPTER_SEQUENCE_MISMATCH"
        for finding in manifest["findings"]
    )


def test_narrative_page_evidence_refs_must_resolve_to_the_same_ir_slide() -> None:
    ir = _ir()
    contract = _narrative_contract(ir)
    contract["pages"][0]["evidence_refs"] = ["block:s1:unknown"]

    manifest = build_authoring_manifest(
        _request(delivery_scope="complete_deck"), ir, _assessment(),
        narrative_contract=contract,
    )

    assert manifest["status"] == "rejected"
    assert any(
        finding["code"] == "NARRATIVE_EVIDENCE_REF_UNKNOWN"
        and finding["path"] == "/pages/0/evidence_refs/0"
        for finding in manifest["findings"]
    )


def test_narrative_pages_must_cover_ir_slides_once_in_story_order() -> None:
    ir = _ir()
    contract = _narrative_contract(ir)
    contract["pages"].reverse()

    manifest = build_authoring_manifest(
        _request(delivery_scope="complete_deck"), ir, _assessment(),
        narrative_contract=contract,
    )

    assert manifest["status"] == "rejected"
    assert any(
        finding["code"] == "NARRATIVE_PAGE_SEQUENCE_MISMATCH"
        for finding in manifest["findings"]
    )


def test_narrative_assertion_ref_must_point_to_its_ir_slide_message() -> None:
    ir = _ir()
    contract = _narrative_contract(ir)
    contract["pages"][0]["assertion_ref"] = "slide:s2:message"

    manifest = build_authoring_manifest(
        _request(delivery_scope="complete_deck"), ir, _assessment(),
        narrative_contract=contract,
    )

    assert manifest["status"] == "rejected"
    assert any(
        finding["code"] == "NARRATIVE_ASSERTION_REF_MISMATCH"
        and finding["path"] == "/pages/0/assertion_ref"
        for finding in manifest["findings"]
    )


def test_nonfinal_narrative_page_requires_an_explicit_transition() -> None:
    ir = _ir()
    contract = _narrative_contract(ir)
    contract["pages"][0]["transition_to_next"] = None

    manifest = build_authoring_manifest(
        _request(delivery_scope="complete_deck"), ir, _assessment(),
        narrative_contract=contract,
    )

    assert manifest["status"] == "rejected"
    assert any(
        finding["code"] == "NARRATIVE_TRANSITION_REQUIRED"
        and finding["path"] == "/pages/0/transition_to_next"
        for finding in manifest["findings"]
    )


def test_plan_bespoke_cli_writes_manifest_without_compiling_standard_deck(tmp_path: Path) -> None:
    request_path = tmp_path / "request.json"
    ir_path = tmp_path / "ir.json"
    assessment_path = tmp_path / "assessment.json"
    output_path = tmp_path / "authoring-manifest.json"
    request_path.write_text(json.dumps(_request()), encoding="utf-8")
    ir_path.write_text(json.dumps(_ir()), encoding="utf-8")
    assessment_path.write_text(json.dumps(_assessment()), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable, "-m", "engine", "plan-bespoke",
            "--request", str(request_path), "--ir", str(ir_path),
            "--content-assessment", str(assessment_path),
            "--json-out", str(output_path),
        ],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    manifest = json.loads(output_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "ready_for_authoring"
    assert manifest["requires_standard_base_deck"] is False
    assert not (tmp_path / "deck.pptx").exists()


def test_plan_bespoke_cli_accepts_a_hash_bound_complete_deck_narrative_contract(tmp_path: Path) -> None:
    request_path = tmp_path / "request.json"
    ir_path = tmp_path / "ir.json"
    assessment_path = tmp_path / "assessment.json"
    narrative_path = tmp_path / "narrative-contract.json"
    output_path = tmp_path / "authoring-manifest.json"
    ir = _ir()
    request_path.write_text(
        json.dumps(_request(delivery_scope="complete_deck")), encoding="utf-8",
    )
    ir_path.write_text(json.dumps(ir), encoding="utf-8")
    assessment_path.write_text(json.dumps(_assessment()), encoding="utf-8")
    narrative_path.write_text(json.dumps(_narrative_contract(ir)), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable, "-m", "engine", "plan-bespoke",
            "--request", str(request_path), "--ir", str(ir_path),
            "--content-assessment", str(assessment_path),
            "--narrative-contract", str(narrative_path),
            "--json-out", str(output_path),
        ],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    manifest = json.loads(output_path.read_text(encoding="utf-8"))
    assert manifest["delivery_scope"] == "complete_deck"
    assert manifest["narrative_contract"]["contract_id"] == "management-review-narrative"

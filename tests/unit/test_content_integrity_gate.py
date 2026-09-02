from __future__ import annotations

import pytest

from engine.content_integrity_gate import evaluate_template_content_integrity
from engine.manuscript_component_planner import build_manuscript_component_composition


def _unit(
    evidence_id: str,
    *,
    salience: float,
    must_keep: bool,
    kind: str = "claim",
) -> dict:
    source_id, loc = evidence_id.split(":", 1)
    return {
        "evidence_id": evidence_id,
        "source_ref": {"source_id": source_id, "loc": loc},
        "kind": kind,
        "text": evidence_id,
        "entities": [],
        "numbers": ([{"value": "36%", "unit": "%", "period": None}]
                    if kind == "metric" else []),
        "relations": [],
        "salience": salience,
        "must_keep": must_keep,
        "exhibit_id": None,
    }


def _ledger() -> dict:
    return {
        "schema_version": "1.0.0",
        "sources": [{"source_id": "src", "sha256": "sha256:fixed"}],
        "evidence_units": [
            _unit(
                "src:para_1", salience=10.0, must_keep=True, kind="metric",
            ),
            _unit("src:para_2", salience=1.0, must_keep=False),
        ],
    }


def _bindings(selected: list[str]) -> dict:
    return {"slides": [{
        "id": "growth",
        "archetype": "body",
        "assertion": "Revenue increased",
        "evidence_ids": selected,
        "required_evidence_ids": ["src:para_1"],
        "omissions": [],
        "title": "Revenue increased",
        "items": [{"title": "Growth", "detail": "Revenue increased"}],
    }]}


def test_gate_rejects_missing_required_and_low_weighted_coverage() -> None:
    result = evaluate_template_content_integrity(
        _bindings(["src:para_2"]),
        _ledger(),
    )

    assert result["status"] == "fail"
    assert {issue["code"] for issue in result["issues"]} >= {
        "REQUIRED_EVIDENCE_MISSING",
        "WEIGHTED_COVERAGE_BELOW_FLOOR",
        "NUMERIC_EVIDENCE_MISSING",
    }


def test_gate_passes_complete_source_backed_contract() -> None:
    result = evaluate_template_content_integrity(
        _bindings(["src:para_1", "src:para_2"]),
        _ledger(),
    )

    assert result["status"] == "pass"
    assert result["issues"] == []
    assert result["coverage"]["weighted_ratio"] == 1.0


def test_delivery_planner_refuses_without_evidence_ledger() -> None:
    with pytest.raises(ValueError, match="CONTENT_INTEGRITY_LEDGER_REQUIRED"):
        build_manuscript_component_composition(
            {"status": "reviewed", "source": {"slide_count": 1}, "components": []},
            _bindings(["src:para_1", "src:para_2"]),
            {"slides": [{
                "purpose": "growth",
                "layout_rationale": {"layout_pattern": "three conclusion cards"},
            }]},
            enforce_content_integrity=True,
        )


def test_delivery_planner_records_passing_integrity_report() -> None:
    atlas = {
        "status": "reviewed",
        "source": {"slide_count": 1},
        "components": [{
            "component_id": "cards",
            "family": "icon_card_grid",
            "slide_index": 1,
            "semantic_uses": ["icon capability cards"],
            "groups": [{
                "role": "segment", "scope": "item",
                "members": [{"shape_name": "card"}],
            }, {
                "role": "label", "scope": "item", "bind_field": "title",
                "members": [{"shape_name": "title"}],
            }, {
                "role": "label", "scope": "item", "bind_field": "detail",
                "members": [{"shape_name": "detail"}],
            }],
            "parameters": {"element_count": {"minimum": 1, "maximum": 1}},
        }],
    }
    composition = build_manuscript_component_composition(
        atlas,
        _bindings(["src:para_1", "src:para_2"]),
        {"slides": [{
            "purpose": "growth",
            "layout_rationale": {"layout_pattern": "three conclusion cards"},
        }]},
        evidence_ledger=_ledger(),
        enforce_content_integrity=True,
    )

    assert composition["content_integrity"]["status"] == "pass"

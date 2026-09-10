from __future__ import annotations

import pytest

from engine.content_integrity_gate import evaluate_template_content_integrity
from engine.evidence_ledger import build_evidence_ledger
from engine.manuscript_component_planner import build_manuscript_component_composition
from engine.structural_parser import parse_markdown


THREE_SECTION_REPORT = """\
# Growth review

## Demand

Enterprise demand remains concentrated in regulated industries.

## Conversion

Qualified-pipeline conversion reached 36% in the review period.

## Retention

Renewal interviews identify implementation support as the main retention driver.
"""


def _bindings(evidence_ids: list[str]) -> dict:
    return {"slides": [{
        "id": "growth_review",
        "archetype": "body",
        "assertion": "Demand and retention are linked to regulated-industry needs.",
        "evidence_ids": evidence_ids,
        "required_evidence_ids": [],
        "omissions": [],
        "title": "Growth review",
        "items": [{
            "title": "Observed demand and retention",
            "detail": "Evidence is preserved from the source report.",
        }],
    }]}


def test_template_delivery_rejects_middle_section_omission() -> None:
    docs = {"src": parse_markdown(THREE_SECTION_REPORT, "src")}
    ledger = build_evidence_ledger(docs)
    bindings = _bindings(["src:para_1", "src:para_3"])

    result = evaluate_template_content_integrity(bindings, ledger)

    assert result["status"] == "fail"
    assert "src:para_2" in result["coverage"]["missing_required_evidence_ids"]
    assert "src:para_2" in result["coverage"]["missing_numeric_evidence_ids"]


def test_template_delivery_accepts_complete_generated_report() -> None:
    docs = {"src": parse_markdown(THREE_SECTION_REPORT, "src")}
    ledger = build_evidence_ledger(docs)
    evidence_ids = [unit["evidence_id"] for unit in ledger["evidence_units"]]

    result = evaluate_template_content_integrity(
        _bindings(evidence_ids), ledger,
    )

    assert result["status"] == "pass"
    assert result["coverage"]["weighted_ratio"] == 1.0
    assert result["coverage"]["required_ratio"] == 1.0
    assert result["coverage"]["numeric_ratio"] == 1.0


def test_delivery_candidate_rejects_repeated_card_family_after_content_passes() -> None:
    docs = {"src": parse_markdown(THREE_SECTION_REPORT, "src")}
    ledger = build_evidence_ledger(docs)
    evidence_ids = [unit["evidence_id"] for unit in ledger["evidence_units"]]
    bindings = {"slides": [{
        "id": f"body_{index}", "archetype": "body",
        "assertion": f"Source-backed claim {index}",
        "evidence_ids": evidence_ids, "required_evidence_ids": [], "omissions": [],
        "items": [{"title": f"Claim {index}", "detail": "Source-backed detail"}],
    } for index in range(1, 4)]}
    atlas = {"status": "reviewed", "source": {"slide_count": 1}, "components": [{
        "component_id": "cards", "family": "icon_card_grid", "slide_index": 1,
        "semantic_uses": ["icon capability cards"],
        "groups": [{"role": "segment", "scope": "item", "members": [{"shape_name": "card"}]},
                   {"role": "label", "scope": "item", "bind_field": "title", "members": [{"shape_name": "title"}]},
                   {"role": "label", "scope": "item", "bind_field": "detail", "members": [{"shape_name": "detail"}]}],
        "parameters": {"element_count": {"minimum": 1, "maximum": 1}},
    }]}
    storyboard = {"slides": [{"purpose": f"body_{index}", "layout_rationale": {"layout_pattern": "three conclusion cards"}} for index in range(1, 4)]}

    with pytest.raises(ValueError, match="COMPONENT_DIVERSITY_FAILED"):
        build_manuscript_component_composition(
            atlas, bindings, storyboard, evidence_ledger=ledger,
            enforce_content_integrity=True,
        )

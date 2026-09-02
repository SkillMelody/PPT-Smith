from __future__ import annotations

from engine.evidence_ledger import build_evidence_ledger, validate_evidence_ledger
from engine.structural_parser import parse_markdown


def test_evidence_ledger_builds_stable_source_backed_units() -> None:
    doc = parse_markdown(
        "# Report\n\n## Growth\n\nRevenue rose 36%.\n\n"
        "| Region | Growth |\n| --- | --- |\n| Global | 52% |",
        "src",
    )

    first = build_evidence_ledger({"src": doc}, {"src": "sha256:fixed"})
    second = build_evidence_ledger({"src": doc}, {"src": "sha256:fixed"})

    assert first == second
    assert first["sources"] == [{"source_id": "src", "sha256": "sha256:fixed"}]
    units = {unit["evidence_id"]: unit for unit in first["evidence_units"]}
    assert units["src:para_1"]["kind"] == "metric"
    assert units["src:para_1"]["numbers"] == [{
        "value": "36%", "unit": "%", "period": None,
    }]
    assert units["src:para_1"]["must_keep"] is True
    assert units["src:table_1"]["kind"] == "exhibit"
    assert units["src:table_1"]["exhibit_id"] == "src:table_1"
    assert validate_evidence_ledger(first) == []


def test_evidence_ledger_rejects_duplicate_ids() -> None:
    unit = {
        "evidence_id": "src:para_99",
        "source_ref": {"source_id": "src", "loc": "para_99"},
        "kind": "claim",
        "text": "missing",
        "entities": [],
        "numbers": [],
        "relations": [],
        "salience": 1.0,
        "must_keep": False,
        "exhibit_id": None,
    }
    ledger = {
        "schema_version": "1.0.0",
        "sources": [{"source_id": "src", "sha256": "sha256:fixed"}],
        "evidence_units": [unit, dict(unit)],
    }

    assert {issue["code"] for issue in validate_evidence_ledger(ledger)} == {
        "EVIDENCE_ID_DUPLICATE",
    }


def test_evidence_ledger_rejects_invalid_source_and_exhibit_contract() -> None:
    ledger = {
        "schema_version": "1.0.0",
        "sources": [{"source_id": "src", "sha256": "sha256:fixed"}],
        "evidence_units": [{
            "evidence_id": "other:bad",
            "source_ref": {"source_id": "other", "loc": "bad"},
            "kind": "exhibit",
            "text": "Exhibit",
            "entities": [],
            "numbers": [],
            "relations": [],
            "salience": 0,
            "must_keep": True,
            "exhibit_id": None,
        }],
    }

    assert {issue["code"] for issue in validate_evidence_ledger(ledger)} == {
        "EVIDENCE_SOURCE_UNKNOWN",
        "EVIDENCE_ANCHOR_INVALID",
        "EVIDENCE_SALIENCE_INVALID",
        "EXHIBIT_ID_REQUIRED",
    }

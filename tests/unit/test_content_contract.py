from __future__ import annotations

from engine.content_contract import validate_content_contracts
from engine.coverage import evidence_coverage_report


def _unit(
    evidence_id: str,
    *,
    kind: str = "claim",
    salience: float = 1.0,
    must_keep: bool = False,
    exhibit_id: str | None = None,
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
        "exhibit_id": exhibit_id,
    }


def _ledger(units: list[dict]) -> dict:
    return {
        "schema_version": "1.0.0",
        "sources": [{"source_id": "src", "sha256": "sha256:fixed"}],
        "evidence_units": units,
    }


def test_body_contract_requires_assertion_and_known_evidence() -> None:
    ledger = _ledger([_unit("src:para_1", must_keep=True)])
    bindings = {"slides": [{
        "id": "growth",
        "archetype": "body",
        "assertion": "",
        "evidence_ids": ["src:para_99"],
        "required_evidence_ids": ["src:para_1"],
        "omissions": [],
    }]}

    assert {issue["code"] for issue in validate_content_contracts(bindings, ledger)} == {
        "SLIDE_ASSERTION_MISSING",
        "EVIDENCE_ID_UNKNOWN",
        "REQUIRED_EVIDENCE_MISSING",
    }


def test_evidence_coverage_reports_weighted_numeric_and_exhibit_recall() -> None:
    ledger = _ledger([
        _unit("src:para_1", kind="metric", salience=2.0, must_keep=True),
        _unit(
            "src:table_1", kind="exhibit", salience=3.0, must_keep=True,
            exhibit_id="src:table_1",
        ),
        _unit("src:para_2", kind="claim", salience=1.0),
    ])
    bindings = {"slides": [{
        "id": "growth",
        "archetype": "body",
        "assertion": "Revenue increased",
        "evidence_ids": ["src:para_1"],
        "required_evidence_ids": ["src:para_1"],
        "omissions": [{
            "evidence_id": "src:table_1",
            "reason": "Appendix exhibit",
        }],
    }]}

    report = evidence_coverage_report(bindings, ledger)

    assert report["weighted_ratio"] == 0.3333
    assert report["required_ratio"] == 1.0
    assert report["numeric_ratio"] == 1.0
    assert report["exhibit_ratio"] == 1.0
    assert report["uncovered_evidence_ids"] == ["src:para_2"]
    assert report["omitted_evidence_ids"] == ["src:table_1"]


def test_contract_rejects_unexplained_exhibit_omission() -> None:
    ledger = _ledger([
        _unit(
            "src:table_1", kind="exhibit", salience=3.0, must_keep=True,
            exhibit_id="src:table_1",
        ),
    ])
    bindings = {"slides": [{
        "id": "method",
        "archetype": "method",
        "assertion": "The source contains one exhibit",
        "evidence_ids": [],
        "required_evidence_ids": [],
        "omissions": [{"evidence_id": "src:table_1", "reason": "  "}],
    }]}

    assert {issue["code"] for issue in validate_content_contracts(bindings, ledger)} == {
        "SLIDE_EVIDENCE_MISSING",
        "EXHIBIT_OMISSION_UNEXPLAINED",
        "REQUIRED_EVIDENCE_MISSING",
    }


def test_cover_contract_uses_explicit_archetype_exception() -> None:
    bindings = {"slides": [{
        "id": "cover",
        "archetype": "cover",
        "assertion": "",
        "evidence_ids": [],
        "required_evidence_ids": [],
        "omissions": [],
    }]}

    assert validate_content_contracts(bindings, _ledger([])) == []

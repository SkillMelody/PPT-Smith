"""Fail-closed content-integrity policy for Template delivery candidates."""

from __future__ import annotations

from .content_contract import validate_content_contracts
from .coverage import evidence_coverage_report


DEFAULT_TEMPLATE_CONTENT_POLICY = {
    "weighted_ratio": 0.90,
    "required_ratio": 1.0,
    "numeric_ratio": 0.95,
    "exhibit_ratio": 1.0,
}

_COVERAGE_CODES = {
    "weighted_ratio": "WEIGHTED_COVERAGE_BELOW_FLOOR",
    "required_ratio": "REQUIRED_EVIDENCE_MISSING",
    "numeric_ratio": "NUMERIC_EVIDENCE_MISSING",
    "exhibit_ratio": "EXHIBIT_OMISSION_UNEXPLAINED",
}


def _coverage_issues(coverage: dict, policy: dict) -> list[dict]:
    issues: list[dict] = []
    for field, code in _COVERAGE_CODES.items():
        actual = float(coverage.get(field, 0.0))
        required = float(policy[field])
        if actual < required:
            issues.append({
                "code": code,
                "metric": field,
                "actual": actual,
                "required": required,
            })
    return issues


def evaluate_template_content_integrity(
    content_bindings: dict,
    ledger: dict,
    policy: dict | None = None,
) -> dict:
    """Evaluate contracts and evidence coverage without mutating inputs."""
    effective = {**DEFAULT_TEMPLATE_CONTENT_POLICY, **(policy or {})}
    contract_issues = validate_content_contracts(content_bindings, ledger)
    coverage = evidence_coverage_report(content_bindings, ledger)
    issues = [*contract_issues, *_coverage_issues(coverage, effective)]
    return {
        "status": "pass" if not issues else "fail",
        "policy": effective,
        "coverage": coverage,
        "issues": issues,
    }

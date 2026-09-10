"""Hash-bound ingestion gate for an external human or vision-model review."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha(payload: dict) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _reject(code: str, **extra) -> dict:
    return {"ok": False, "status": "rejected", "code": code, **extra}


def apply_visual_review(authoring_report_path: str | Path, review: dict) -> dict:
    """Validate an external review against exactly one rendered authoring run."""
    path = Path(authoring_report_path)
    try:
        authoring = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _reject("AUTHORING_REPORT_UNREADABLE", error=str(exc))
    if authoring.get("status") != "visual_unreviewed" or not authoring.get("ok"):
        return _reject("AUTHORING_RESULT_NOT_REVIEWABLE")
    if authoring.get("visual_quality", {}).get("status") != "pass":
        return _reject("VISUAL_REVIEW_VISUAL_FLOOR_REQUIRED")
    if review.get("schema_version") != "1.0.0" or review.get("status") not in {"approved", "revise", "rejected"}:
        return _reject("VISUAL_REVIEW_INVALID")
    deck = Path(authoring.get("deck", ""))
    render = path.parent / "render-report.json"
    if not deck.is_file() or not render.is_file() or authoring.get("render", {}).get("status") != "passed":
        return _reject("VISUAL_REVIEW_RENDER_EVIDENCE_REQUIRED")
    if review.get("deck_sha256") != _sha(deck):
        return _reject("VISUAL_REVIEW_DECK_HASH_MISMATCH")
    if review.get("render_report_sha256") != _sha(render):
        return _reject("VISUAL_REVIEW_RENDER_HASH_MISMATCH")
    reviewer = review.get("reviewer", {})
    if not all(isinstance(reviewer.get(key), str) and reviewer[key] for key in ("provider", "model", "method")):
        return _reject("VISUAL_REVIEW_REVIEWER_REQUIRED")
    round_number = review.get("round")
    if not isinstance(round_number, int) or round_number < 1:
        return _reject("VISUAL_REVIEW_ROUND_INVALID")
    if round_number > 2:
        return _reject("VISUAL_REVIEW_MAX_REFINEMENTS_EXCEEDED")
    findings = review.get("findings")
    if not isinstance(findings, list):
        return _reject("VISUAL_REVIEW_FINDINGS_INVALID")
    if review["status"] == "approved" and findings:
        return _reject("VISUAL_REVIEW_APPROVAL_HAS_FINDINGS")
    if review["status"] != "approved" and not findings:
        return _reject("VISUAL_REVIEW_FINDINGS_REQUIRED")
    return {
        "ok": review["status"] == "approved",
        "status": "visual_approved" if review["status"] == "approved" else "refinement_required",
        "deck": str(deck), "review_round": round_number,
        "visual_review": review,
    }


def apply_template_visual_review(strict_report_path: str | Path, review: dict) -> dict:
    """Approve a Template candidate only against its exact deck and render."""
    path = Path(strict_report_path)
    try:
        strict = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _reject("STRICT_TEMPLATE_REPORT_UNREADABLE", error=str(exc))
    if strict.get("status") != "strict_candidate_verified" or not strict.get("ok"):
        return _reject("STRICT_TEMPLATE_RESULT_NOT_REVIEWABLE")
    for field in ("native_visual_floor", "template_visual_quality"):
        if strict.get(field, {}).get("status") != "pass":
            return _reject("TEMPLATE_VISUAL_FLOOR_REQUIRED", field=field)
    if review.get("schema_version") != "1.0.0" or review.get("status") not in {
        "approved", "revise", "rejected",
    }:
        return _reject("VISUAL_REVIEW_INVALID")
    deck = Path(strict.get("output_pptx", ""))
    render = strict.get("render")
    if not deck.is_file() or not isinstance(render, dict) or render.get("status") != "passed":
        return _reject("VISUAL_REVIEW_RENDER_EVIDENCE_REQUIRED")
    if review.get("deck_sha256") != _sha(deck):
        return _reject("VISUAL_REVIEW_DECK_HASH_MISMATCH")
    if review.get("render_report_sha256") != _canonical_sha(render):
        return _reject("VISUAL_REVIEW_RENDER_HASH_MISMATCH")
    reviewer = review.get("reviewer", {})
    if not all(
        isinstance(reviewer.get(key), str) and reviewer[key]
        for key in ("provider", "model", "method")
    ):
        return _reject("VISUAL_REVIEW_REVIEWER_REQUIRED")
    round_number = review.get("round")
    if not isinstance(round_number, int) or round_number < 1:
        return _reject("VISUAL_REVIEW_ROUND_INVALID")
    if round_number > 2:
        return _reject("VISUAL_REVIEW_MAX_REFINEMENTS_EXCEEDED")
    findings = review.get("findings")
    if not isinstance(findings, list):
        return _reject("VISUAL_REVIEW_FINDINGS_INVALID")
    if review["status"] == "approved" and findings:
        return _reject("VISUAL_REVIEW_APPROVAL_HAS_FINDINGS")
    if review["status"] != "approved" and not findings:
        return _reject("VISUAL_REVIEW_FINDINGS_REQUIRED")
    approved = review["status"] == "approved"
    return {
        "ok": approved,
        "status": "final_delivery_ready" if approved else "refinement_required",
        "route": "template",
        "deck": str(deck),
        "review_round": round_number,
        "visual_review": review,
    }

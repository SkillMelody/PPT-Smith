from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

from engine.visual_review import (
    _canonical_sha,
    apply_template_visual_review,
    apply_visual_review,
)

ROOT = Path(__file__).resolve().parents[2]


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _authoring(tmp_path: Path) -> Path:
    deck = tmp_path / "deck.pptx"
    render = tmp_path / "render-report.json"
    deck.write_bytes(b"native deck")
    render.write_text(json.dumps({"status": "passed", "slides": [{"slide_index": 1}]}), encoding="utf-8")
    authoring = tmp_path / "authoring-report.json"
    authoring.write_text(json.dumps({
        "ok": True, "status": "visual_unreviewed", "deck": str(deck),
        "render": {"status": "passed"},
        "visual_quality": {"status": "pass", "findings": []},
        "visual_review": "required_not_run",
    }), encoding="utf-8")
    return authoring


def _review(authoring: Path, *, status: str = "approved", round_number: int = 1) -> dict:
    report = json.loads(authoring.read_text(encoding="utf-8"))
    deck = Path(report["deck"])
    render = deck.parent / "render-report.json"
    return {
        "schema_version": "1.0.0", "status": status, "round": round_number,
        "deck_sha256": _sha(deck), "render_report_sha256": _sha(render),
        "reviewer": {"provider": "test", "model": "vision-1", "method": "visual_model"},
        "findings": [] if status == "approved" else [{
            "slide_index": 1, "severity": "warning", "criterion": "density",
            "evidence": "Large empty region in lower third.", "instruction": "Use the space for evidence.",
        }],
    }


def test_visual_review_approves_only_a_hash_bound_rendered_authoring_result(tmp_path: Path) -> None:
    authoring = _authoring(tmp_path)

    result = apply_visual_review(authoring, _review(authoring))

    assert result["ok"] is True
    assert result["status"] == "visual_approved"
    assert result["visual_review"]["reviewer"]["model"] == "vision-1"


def test_visual_review_rejects_legacy_authoring_without_visual_floor_evidence(tmp_path: Path) -> None:
    authoring = _authoring(tmp_path)
    payload = json.loads(authoring.read_text(encoding="utf-8"))
    payload.pop("visual_quality")
    authoring.write_text(json.dumps(payload), encoding="utf-8")

    result = apply_visual_review(authoring, _review(authoring))

    assert result["ok"] is False
    assert result["code"] == "VISUAL_REVIEW_VISUAL_FLOOR_REQUIRED"


def test_visual_review_rejects_review_for_different_deck(tmp_path: Path) -> None:
    authoring = _authoring(tmp_path)
    review = _review(authoring)
    review["deck_sha256"] = "sha256:" + "0" * 64

    result = apply_visual_review(authoring, review)

    assert result["ok"] is False
    assert result["code"] == "VISUAL_REVIEW_DECK_HASH_MISMATCH"


def test_visual_review_limits_refinement_rounds_without_claiming_approval(tmp_path: Path) -> None:
    authoring = _authoring(tmp_path)

    result = apply_visual_review(authoring, _review(authoring, status="revise", round_number=3))

    assert result["ok"] is False
    assert result["code"] == "VISUAL_REVIEW_MAX_REFINEMENTS_EXCEEDED"


def test_review_bespoke_cli_writes_visual_approval(tmp_path: Path) -> None:
    authoring = _authoring(tmp_path)
    review_path = tmp_path / "review.json"
    output = tmp_path / "review-result.json"
    review_path.write_text(json.dumps(_review(authoring)), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, "-m", "engine", "review-bespoke", "--authoring-report", str(authoring),
         "--review", str(review_path), "--json-out", str(output)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "visual_approved"


def _strict_report(tmp_path: Path) -> Path:
    deck = tmp_path / "template-candidate.pptx"
    deck.write_bytes(b"native template deck")
    render = {"status": "passed", "slides": [{"slide_index": 1, "blank_score": 0.4}]}
    report = tmp_path / "strict-report.json"
    report.write_text(json.dumps({
        "ok": True,
        "status": "strict_candidate_verified",
        "output_pptx": str(deck),
        "render": render,
        "native_visual_floor": {"status": "pass", "findings": []},
        "template_visual_quality": {"status": "pass", "issues": []},
    }), encoding="utf-8")
    return report


def _template_review(report: Path, *, status: str = "approved") -> dict:
    strict = json.loads(report.read_text(encoding="utf-8"))
    return {
        "schema_version": "1.0.0",
        "status": status,
        "round": 1,
        "deck_sha256": _sha(Path(strict["output_pptx"])),
        "render_report_sha256": _canonical_sha(strict["render"]),
        "reviewer": {
            "provider": "test",
            "model": "vision-1",
            "method": "rendered_contact_sheet",
        },
        "findings": [] if status == "approved" else [{
            "slide_index": 1,
            "criterion": "visual hierarchy",
            "instruction": "Increase the quantitative focal point.",
        }],
    }


def test_template_visual_review_is_hash_bound_and_marks_final_delivery_ready(
    tmp_path: Path,
) -> None:
    report = _strict_report(tmp_path)

    result = apply_template_visual_review(report, _template_review(report))

    assert result["ok"] is True
    assert result["status"] == "final_delivery_ready"


def test_template_visual_review_rejects_a_different_render_fingerprint(
    tmp_path: Path,
) -> None:
    report = _strict_report(tmp_path)
    review = _template_review(report)
    review["render_report_sha256"] = "sha256:" + "0" * 64

    result = apply_template_visual_review(report, review)

    assert result["ok"] is False
    assert result["code"] == "VISUAL_REVIEW_RENDER_HASH_MISMATCH"

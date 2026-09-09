from __future__ import annotations

from engine.model_authored_quality import evaluate_model_authored_quality


def _slide(**overrides) -> dict:
    return {
        "id": "s1",
        "title": "Workflow redesign converts adoption into enterprise value",
        "message": "Value depends on redesigning the workflow, not deploying isolated tools.",
        "slide_role": "content",
        "blocks": [{
            "id": "findings",
            "role": "list",
            "items": [
                {"text": "Redesign the end-to-end workflow", "detail": "Remove handoff friction."},
                {"text": "Scale with accountable owners", "detail": "Track value and adoption."},
            ],
        }],
        **overrides,
    }


def test_model_authored_quality_accepts_complete_visible_expression() -> None:
    report = evaluate_model_authored_quality({"slides": [_slide()]})

    assert report["status"] == "pass"
    assert report["issues"] == []


def test_model_authored_quality_rejects_ellipsis_and_source_page_screenshot() -> None:
    slide = _slide(
        title="Workflow redesign…",
        blocks=[{
            "id": "page",
            "role": "image",
            "asset_ref": "page-12.png",
            "asset_kind": "page_screenshot",
            "reconstructable": False,
            "crop_audit": {
                "includes_page_header": True,
                "includes_page_footer": True,
                "includes_navigation": True,
                "includes_body_prose": True,
                "text_area_ratio": 0.6,
            },
        }],
    )

    report = evaluate_model_authored_quality({"slides": [slide]})
    codes = {issue["code"] for issue in report["issues"]}

    assert report["status"] == "fail"
    assert {
        "VISIBLE_CONTENT_ELLIPSIS",
        "SOURCE_PAGE_SCREENSHOT_FORBIDDEN",
        "SOURCE_ILLUSTRATION_CROP_CONTAMINATED",
    } <= codes


def test_reconstructable_data_figure_requires_native_chart() -> None:
    slide = _slide(blocks=[{
        "id": "chart-image",
        "role": "image",
        "asset_ref": "chart.png",
        "asset_kind": "data_figure",
        "reconstructable": True,
        "crop_audit": {
            "includes_page_header": False,
            "includes_page_footer": False,
            "includes_navigation": False,
            "includes_body_prose": False,
        },
    }])

    report = evaluate_model_authored_quality({"slides": [slide]})

    assert any(issue["code"] == "NATIVE_DATA_VISUAL_REQUIRED" for issue in report["issues"])


def test_model_authored_quality_rejects_unresolved_generator_values() -> None:
    report = evaluate_model_authored_quality({
        "slides": [_slide(blocks=[{
            "id": "findings",
            "role": "list",
            "items": [{"text": "undefined", "detail": "A value failed to bind."}],
        }])],
    })

    assert report["status"] == "fail"
    assert any(
        issue["code"] == "MODEL_AUTHORED_PLACEHOLDER_TEXT"
        for issue in report["issues"]
    )

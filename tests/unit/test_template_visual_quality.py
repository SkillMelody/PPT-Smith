from __future__ import annotations

from engine.template_visual_quality import evaluate_template_visual_quality


def test_visual_quality_uses_archetype_specific_density_floors() -> None:
    report = evaluate_template_visual_quality([
        {
            "slide_id": "S01", "archetype": "cover",
            "visible_text_chars": 35, "chart_count": 0,
            "semantic_element_count": 1, "families": ["icon_card_grid"],
            "blank_score": 0.70,
        },
        {
            "slide_id": "S02", "archetype": "body",
            "visible_text_chars": 42, "chart_count": 4,
            "semantic_element_count": 4, "families": ["kpi_chart_card"],
            "blank_score": 0.80,
        },
        {
            "slide_id": "S03", "archetype": "body",
            "visible_text_chars": 55, "chart_count": 0,
            "semantic_element_count": 4, "families": ["pyramid"],
            "blank_score": 0.75,
        },
        {
            "slide_id": "S04", "archetype": "body",
            "visible_text_chars": 85, "chart_count": 0,
            "semantic_element_count": 3, "families": ["card_grid"],
            "blank_score": 0.82,
        },
    ])

    assert report["status"] == "pass"
    assert [page["density_role"] for page in report["pages"]] == [
        "cover", "data", "relationship", "body",
    ]


def test_visual_quality_rejects_empty_body_and_excessive_whitespace() -> None:
    report = evaluate_template_visual_quality([
        {
            "slide_id": "S09", "archetype": "body",
            "visible_text_chars": 20, "chart_count": 0,
            "semantic_element_count": 2, "families": ["card_grid"],
            "blank_score": 0.94,
        },
    ])

    assert report["status"] == "fail"
    assert {issue["code"] for issue in report["issues"]} == {
        "VISUAL_CONTENT_DENSITY_BELOW_FLOOR",
        "VISUAL_PAGE_TOO_BLANK",
    }


def test_visual_quality_rejects_declared_information_that_is_not_rendered() -> None:
    report = evaluate_template_visual_quality([{
        "slide_id": "S10",
        "archetype": "body",
        "visible_text_chars": 240,
        "chart_count": 0,
        "semantic_element_count": 6,
        "families": ["card_grid"],
        "blank_score": 0.70,
        "bound_semantic_object_count": 2,
        "declared_information_unit_count": 8,
    }])

    assert report["status"] == "fail"
    assert any(
        issue["code"] == "VISUAL_DECLARED_INFORMATION_UNDER_RENDERED"
        for issue in report["issues"]
    )

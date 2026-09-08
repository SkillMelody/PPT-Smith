from __future__ import annotations

from engine.template_page_composition import (
    evaluate_template_page_compositions,
    template_boundary_capabilities,
)


def _atlas() -> dict:
    return {
        "status": "reviewed",
        "components": [{
            "component_id": "template.chart",
            "granularity": "micro",
            "page_guidance": {
                "can_stand_alone": False,
                "supported_page_roles": ["body"],
                "minimum_information_units": 2,
                "recommended_page_recipes": ["chart-with-insights"],
                "required_companion_roles": ["interpretation"],
                "recommended_companion_families": ["insight_card"],
                "annotation_requirements": ["value labels"],
                "prohibited_scenarios": ["chart alone on a page"],
            },
        }],
    }


def _body_page(slide_id: str, *, recipe: str, variant: str) -> dict:
    return {
        "slide_id": slide_id,
        "page_composition": {
            "page_role": "body",
            "recipe": recipe,
            "variant": variant,
            "semantic_layers": ["assertion", "primary_evidence", "interpretation"],
            "content_modules": [
                {
                    "module_id": "chart",
                    "role": "primary_evidence",
                    "component_ids": ["template.chart"],
                    "information_unit_count": 3,
                },
                {
                    "module_id": "insight",
                    "role": "interpretation",
                    "component_ids": ["model.support"],
                    "information_unit_count": 2,
                },
            ],
            "key_numbers": [
                {"label": "Current", "value": "34%"},
                {"label": "Target", "value": "72%"},
            ],
            "chart_annotations": ["Target is 38 points above current"],
            "takeaway": "The evidence shows a material gap with a clear operating implication.",
        },
        "components": [
            {"component_id": "template.chart"},
            {"component_id": "model.support"},
        ],
    }


def test_page_composition_rejects_a_component_used_as_the_whole_page() -> None:
    ir = {"slides": [{
        "id": "s1", "slide_role": "content", "charts": [{"id": "c1"}],
        "component_intent": {"data_shape": {"kind": "chart"}},
    }]}
    page = _body_page("s1", recipe="data-hero", variant="single-chart")
    page["page_composition"]["content_modules"].pop()
    page["page_composition"]["semantic_layers"] = ["assertion", "primary_evidence"]
    page["page_composition"]["key_numbers"] = []
    page["page_composition"]["chart_annotations"] = []

    report = evaluate_template_page_compositions(ir, _atlas(), {"slides": [page]})

    codes = {issue["code"] for issue in report["issues"]}
    assert "TEMPLATE_PAGE_SINGLE_COMPONENT_SHELL" in codes
    assert "TEMPLATE_PAGE_SEMANTIC_LAYERS_INCOMPLETE" in codes
    assert "TEMPLATE_QUANTITATIVE_PAGE_KEY_NUMBERS_REQUIRED" in codes
    assert "TEMPLATE_QUANTITATIVE_PAGE_ANNOTATION_REQUIRED" in codes


def test_boundary_pages_are_original_when_the_template_has_no_full_page_recipe() -> None:
    atlas = _atlas()
    ir = {"slides": [
        {"id": "cover", "slide_role": "cover"},
        {"id": "close", "slide_role": "closing"},
    ]}
    plan = {"slides": [
        {
            "slide_id": "cover", "components": [{"component_id": "model.cover"}],
            "page_composition": {
                "page_role": "cover", "recipe": "original-cover",
                "variant": "style-derived", "semantic_layers": ["assertion"],
                "content_modules": [], "boundary_strategy": "style_derived_original",
            },
        },
        {
            "slide_id": "close", "components": [{"component_id": "model.close"}],
            "page_composition": {
                "page_role": "closing", "recipe": "original-closing",
                "variant": "style-derived", "semantic_layers": ["assertion"],
                "content_modules": [], "boundary_strategy": "style_derived_original",
            },
        },
    ]}

    report = evaluate_template_page_compositions(ir, atlas, plan)

    assert template_boundary_capabilities(atlas)["has_cover_page_recipe"] is False
    assert template_boundary_capabilities(atlas)["has_closing_page_recipe"] is False
    assert report["status"] == "pass"


def test_deck_rhythm_rejects_repeating_one_visual_pattern() -> None:
    slides = []
    pages = []
    for index in range(10):
        slide_id = f"s{index + 1}"
        slides.append({"id": slide_id, "slide_role": "content"})
        pages.append(_body_page(slide_id, recipe="chart-with-insights", variant="left-chart"))

    report = evaluate_template_page_compositions(
        {"slides": slides}, _atlas(), {"slides": pages},
    )

    codes = {issue["code"] for issue in report["rhythm"]["issues"]}
    assert "TEMPLATE_PAGE_PATTERN_CONSECUTIVE_LIMIT" in codes
    assert "TEMPLATE_PAGE_RECIPE_OVERUSED" in codes
    assert "TEMPLATE_PAGE_RECIPE_DIVERSITY_LOW" in codes

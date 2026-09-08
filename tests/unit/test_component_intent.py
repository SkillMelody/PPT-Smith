from __future__ import annotations

from engine.component_intent import evaluate_component_intents
from engine.component_atlas import validate_model_authoring_atlas


def _atlas() -> dict:
    return {
        "status": "reviewed",
        "components": [{
            "component_id": "template.kpi-card",
            "family": "kpi_chart_card",
            "semantic_uses": ["single KPI comparison"],
            "topologies": ["comparison"],
            "archetypes": ["data"],
            "composition_roles": ["primary"],
            "semantic_contract": {"required_fields": ["title", "metric", "chart"]},
            "text_capacity": {"title": 80, "metric": 40},
            "data_contract": {
                "kinds": ["chart"],
                "chart_types": ["column", "bar"],
                "max_series": 2,
                "max_categories": 8
            },
            "native_fidelity": "exact",
            "parameters": {"element_count": {"minimum": 1, "maximum": 1}},
        }],
    }


def _slide(intent: dict) -> dict:
    return {
        "id": "s1",
        "slide_role": "content",
        "component_intent": intent,
    }


def _intent(**overrides) -> dict:
    return {
        "mode": "template_reuse",
        "semantic_use": "single KPI comparison",
        "element_count": 1,
        "topology": "comparison",
        "required_slots": ["title", "metric", "chart"],
        "archetype": "data",
        "composition_role": "primary",
        "text_requirements": {"title": 60, "metric": 10},
        "data_shape": {
            "kind": "chart", "chart_type": "column",
            "series_count": 1, "category_count": 4,
        },
        "candidate_component_ids": ["template.kpi-card"],
        "selected_component_ids": ["template.kpi-card"],
        **overrides,
    }


def test_component_intent_passes_when_all_feasible_components_are_audited_and_reused() -> None:
    report = evaluate_component_intents({"slides": [_slide(_intent())]}, _atlas())

    assert report["status"] == "pass"
    assert report["eligible_component_coverage"] == 1.0
    assert report["pages"][0]["feasible_components"][0]["component_id"] == (
        "template.kpi-card"
    )


def test_component_intent_rejects_model_authored_fallback_when_template_component_fits() -> None:
    report = evaluate_component_intents({
        "slides": [_slide(_intent(
            mode="model_authored",
            selected_component_ids=[],
            new_component_id="authored.kpi-card",
            style_reference_component_ids=["template.cards"],
        ))],
    }, _atlas())

    assert report["status"] == "fail"
    assert "FEASIBLE_TEMPLATE_COMPONENT_UNUSED" in {
        issue["code"] for issue in report["issues"]
    }


def test_component_intent_allows_model_authored_page_when_every_feasible_component_is_rejected() -> None:
    report = evaluate_component_intents({
        "slides": [_slide(_intent(
            mode="model_authored",
            selected_component_ids=[],
            new_component_id="authored.kpi-card",
            style_reference_component_ids=["template.kpi-card"],
            rejected_candidates=[{
                "component_id": "template.kpi-card",
                "reason_code": "page_fit_incompatible",
                "reason": "The fixed badge cannot fit the required assertion without crowding.",
            }],
        ))],
    }, _atlas())

    assert report["status"] == "pass"
    assert report["justified_model_authored_page_count"] == 1


def test_component_intent_requires_model_authored_component_when_atlas_has_no_match() -> None:
    report = evaluate_component_intents({
        "slides": [_slide(_intent(
            semantic_use="country risk matrix",
            candidate_component_ids=[],
            selected_component_ids=[],
        ))],
    }, _atlas())

    assert report["status"] == "fail"
    assert report["issues"][-1]["code"] == "MODEL_AUTHORED_COMPONENT_REQUIRED"


def test_model_authoring_atlas_requires_rich_component_metadata() -> None:
    assert validate_model_authoring_atlas(_atlas())["status"] == "pass"

    incomplete = _atlas()
    incomplete["components"][0].pop("text_capacity")
    report = validate_model_authoring_atlas(incomplete)

    assert report["status"] == "fail"
    assert any(
        issue["field"] == "text_capacity"
        for issue in report["issues"]
        if issue["code"] == "COMPONENT_METADATA_INCOMPLETE"
    )

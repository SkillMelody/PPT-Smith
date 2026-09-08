from __future__ import annotations

import pytest

from engine.component_composer import build_component_plan


def _atlas() -> dict:
    return {
        "status": "reviewed",
        "components": [{
            "component_id": "unknown-template.cards",
            "family": "card_grid",
            "semantic_uses": ["findings"],
            "topologies": ["comparison"],
            "semantic_contract": {"required_fields": ["title", "detail"]},
            "parameters": {"element_count": {"minimum": 2, "maximum": 4}},
            "text_capacity": {"title": 80, "detail": 160},
            "data_contract": {"kinds": ["none"]},
            "groups": [],
            "adaptation_contract": {
                "content_bbox": {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.4},
                "background": {"policy": "none", "shape_names": []},
                "responsive": {
                    "modes": ["scale_uniform"],
                    "source_aspect_ratio": 2.0,
                    "supported_aspect_ratio": {"minimum": 1.6, "maximum": 2.4},
                },
                "density": {
                    "minimum_information_units": 4,
                    "minimum_label_chars": 12,
                    "minimum_numeric_annotations": 0,
                },
                "preferred_aspect_ratios": [2.0],
                "series_role": "independent",
            },
        }],
    }


def _composition(*, placement: dict, elements: list[dict]) -> dict:
    return {
        "schema_version": "1.0.0",
        "pages": [{
            "destination_slide_index": 1,
            "components": [{
                "component_id": "unknown-template.cards",
                "semantic_use": "findings",
                "topology": "comparison",
                "placement": placement,
                "elements": elements,
            }],
        }],
    }


def test_component_fit_rejects_claimed_full_width_when_native_geometry_cannot_reflow() -> None:
    with pytest.raises(ValueError, match="TEMPLATE_COMPONENT_TARGET_ASPECT_UNSUPPORTED"):
        build_component_plan(_atlas(), _composition(
            placement={"x": 0.1, "y": 0.1, "w": 0.3, "h": 0.7, "require_fill": True},
            elements=[{"title": "Evidence one", "detail": "Detailed finding"},
                      {"title": "Evidence two", "detail": "Detailed implication"}],
        ))


def test_component_fit_rejects_large_cards_with_underfilled_labels() -> None:
    with pytest.raises(ValueError, match="TEMPLATE_COMPONENT_LABEL_DENSITY_LOW"):
        build_component_plan(_atlas(), _composition(
            placement={"x": 0.1, "y": 0.2, "w": 0.8, "h": 0.4},
            elements=[{"title": "A", "detail": "B"}, {"title": "C", "detail": "D"}],
        ))


def test_component_fit_preserves_adaptation_evidence_in_strict_operation() -> None:
    plan = build_component_plan(_atlas(), _composition(
        placement={"x": 0.1, "y": 0.2, "w": 0.8, "h": 0.4},
        elements=[{"title": "Evidence one", "detail": "Detailed finding"},
                  {"title": "Evidence two", "detail": "Detailed implication"}],
    ))

    assert plan["operations"][0]["adaptation"]["series_role"] == "independent"
    assert plan["selections"][0]["adaptation"]["status"] == "pass"

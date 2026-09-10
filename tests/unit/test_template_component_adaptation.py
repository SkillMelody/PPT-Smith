from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches

from engine.component_atlas import build_component_atlas, resolve_component_binding
from engine.template_component_adaptation import evaluate_component_target_fit


def _template(path: Path, *, widescreen: bool = True) -> None:
    presentation = Presentation()
    if not widescreen:
        presentation.slide_width = Inches(10)
        presentation.slide_height = Inches(7.5)
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    background = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.2), Inches(0.4),
        presentation.slide_width - Inches(0.4), Inches(5.8),
    )
    background.name = "sample-local-backdrop"
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(2), Inches(1.5), Inches(5), Inches(2.5),
    )
    card.name = "sample-card"
    label = slide.shapes.add_textbox(Inches(2.4), Inches(2), Inches(4.2), Inches(1.2))
    label.name = "sample-label"
    label.text = "Sample"
    presentation.save(path)


def _review() -> dict:
    return {
        "schema_version": "1.0.0",
        "review": {"state": "reviewed", "reviewer": {"method": "model", "id": "test"}},
        "components": [{
            "component_id": "uploaded-template.component-unknown-to-engine",
            "family": "card_grid",
            "slide_index": 1,
            "semantic_uses": ["key findings"],
            "topologies": ["comparison"],
            "archetypes": ["content"],
            "composition_roles": ["primary"],
            "groups": [
                {"role": "row_background", "shape_names": ["sample-local-backdrop"], "scope": "shared"},
                {"role": "segment", "shape_names": ["sample-card"], "scope": "item", "item_indices": [0]},
                {"role": "label", "bind_field": "title", "shape_names": ["sample-label"], "scope": "item", "item_indices": [0]},
            ],
            "parameters": {"element_count": {"minimum": 1, "maximum": 4}},
            "semantic_contract": {"required_fields": ["title"]},
            "text_capacity": {"title": 80},
            "data_contract": {"kinds": ["none"]},
            "native_fidelity": "exact",
            "renderer": "card_grid",
            "page_guidance": {
                "can_stand_alone": False,
                "supported_page_roles": ["body"],
                "minimum_information_units": 4,
                "recommended_page_recipes": ["cards-with-implication"],
                "required_companion_roles": ["implication"],
                "recommended_companion_families": ["statement"],
                "annotation_requirements": [],
                "prohibited_scenarios": ["single sparse card"],
            },
        }],
    }


def test_atlas_derives_content_decoration_and_oversized_background_policy(tmp_path: Path) -> None:
    template = tmp_path / "unseen-template.pptx"
    _template(template)

    component = build_component_atlas(template, _review())["components"][0]
    contract = component["adaptation_contract"]

    assert contract["content_bbox"]["w"] < contract["background"]["bbox"]["w"]
    assert contract["background"]["policy"] == "strip_on_reuse"
    assert contract["background"]["shape_names"] == ["sample-local-backdrop"]
    assert "reflow_grid" in contract["responsive"]["modes"]
    assert contract["density"]["minimum_information_units"] == 4

    binding = resolve_component_binding({"status": "reviewed", "components": [component]}, {
        "semantic_use": "key findings",
        "element_count": 1,
        "topology": "comparison",
    })
    assert binding["shared_names"] == []
    assert binding["stripped_background_names"] == ["sample-local-backdrop"]


def test_target_fit_uses_component_geometry_not_template_identity(tmp_path: Path) -> None:
    template = tmp_path / "unseen-4x3-template.pptx"
    _template(template, widescreen=False)
    component = build_component_atlas(template, _review())["components"][0]

    assert evaluate_component_target_fit(
        component, {"x": 0.05, "y": 0.2, "w": 0.90, "h": 0.55},
    )["status"] == "pass"

    rigid = dict(component)
    rigid["adaptation_contract"] = {
        **component["adaptation_contract"],
        "responsive": {
            "modes": ["scale_uniform"],
            "source_aspect_ratio": 2.0,
            "supported_aspect_ratio": {"minimum": 1.8, "maximum": 2.2},
        },
    }
    result = evaluate_component_target_fit(
        rigid, {"x": 0.1, "y": 0.1, "w": 0.3, "h": 0.7, "require_fill": True},
    )
    assert result["code"] == "TEMPLATE_COMPONENT_TARGET_ASPECT_UNSUPPORTED"


def test_review_can_override_background_policy_without_brand_specific_logic(tmp_path: Path) -> None:
    template = tmp_path / "dark-template.pptx"
    _template(template)
    review = _review()
    review["components"][0]["adaptation_contract"] = {
        "background": {
            "policy": "retain_component",
            "rationale": "The backdrop is the semantic container for this template.",
        },
        "preferred_aspect_ratios": [1.6, 1.8],
        "series_role": "comparison_anchor",
    }

    contract = build_component_atlas(template, review)["components"][0]["adaptation_contract"]

    assert contract["background"]["policy"] == "retain_component"
    assert contract["preferred_aspect_ratios"] == [1.6, 1.8]
    assert contract["series_role"] == "comparison_anchor"

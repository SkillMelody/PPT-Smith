from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from engine.model_template_composer import build_model_template_composition
from engine.component_composer import build_component_plan


ROOT = Path(__file__).resolve().parents[2]


def _component(component_id: str, family: str) -> dict:
    return {
        "component_id": component_id,
        "family": family,
        "granularity": "micro",
        "slide_index": 1,
        "semantic_uses": ["key findings"],
        "topologies": ["comparison"],
        "archetypes": ["content"],
        "composition_roles": ["primary", "supporting"],
        "semantic_contract": {"required_fields": ["title", "detail"]},
        "text_capacity": {"title": 80, "detail": 180},
        "data_contract": {"kinds": ["none"]},
        "native_fidelity": "exact",
        "parameters": {"element_count": {"minimum": 1, "maximum": 4}},
        "groups": [],
    }


def _atlas() -> dict:
    return {
        "status": "reviewed",
        "source": {"slide_count": 10},
        "components": [
            _component("template.cards", "card_grid"),
            _component("template.metrics", "dual_panel"),
        ],
    }


def _intent() -> dict:
    return {
        "mode": "template_composition",
        "semantic_use": "key findings",
        "element_count": 1,
        "topology": "comparison",
        "required_slots": ["title", "detail"],
        "archetype": "content",
        "text_requirements": {"title": 40, "detail": 100},
        "data_shape": {"kind": "none"},
        "candidate_component_ids": ["template.cards", "template.metrics"],
        "selected_component_ids": ["template.cards", "template.metrics"],
        "rejected_candidates": [],
    }


def _ir() -> dict:
    return {"slides": [{
        "id": "s1",
        "slide_role": "content",
        "component_intent": _intent(),
    }]}


def _model_plan() -> dict:
    def component(component_id: str, x: float) -> dict:
        return {
            "component_id": component_id,
            "placement": {"x": x, "y": 0.2, "w": 0.44, "h": 0.6},
            "payload": {
                "semantic_use": "key findings",
                "element_count": 1,
                "topology": "comparison",
                "required_slots": ["title", "detail"],
                "archetype": "content",
                "text_requirements": {"title": 40, "detail": 100},
                "data_shape": {"kind": "none"},
                "elements": [{"title": "Finding", "detail": "Evidence"}],
            },
        }
    return {
        "schema_version": "1.0.0",
        "slides": [{
            "slide_id": "s1",
            "output_page_index": 1,
            "page_composition": {
                "page_role": "body",
                "recipe": "comparison",
                "variant": "split-evidence-and-implication",
                "semantic_layers": ["assertion", "primary_evidence", "implication"],
                "content_modules": [
                    {
                        "module_id": "evidence",
                        "role": "primary_evidence",
                        "component_ids": ["template.cards"],
                        "information_unit_count": 2,
                    },
                    {
                        "module_id": "implication",
                        "role": "implication",
                        "component_ids": ["template.metrics"],
                        "information_unit_count": 2,
                    },
                ],
                "takeaway": "The comparison resolves into a clear decision implication.",
            },
            "components": [
                component("template.cards", 0.04),
                component("template.metrics", 0.52),
            ],
        }],
    }


def test_model_template_composer_preserves_explicit_multi_component_composition() -> None:
    composition = build_model_template_composition(_ir(), _atlas(), _model_plan())

    assert composition["coverage"]["status"] == "complete"
    assert composition["component_intent"]["eligible_component_coverage"] == 1.0
    page = composition["pages"][0]
    assert page["destination_slide_index"] == 11
    assert [component["component_id"] for component in page["components"]] == [
        "template.cards", "template.metrics",
    ]


def test_model_template_composer_rejects_plan_that_differs_from_declared_selection() -> None:
    plan = _model_plan()
    plan["slides"][0]["components"].pop()

    with pytest.raises(ValueError, match="MODEL_TEMPLATE_SELECTION_MISMATCH"):
        build_model_template_composition(
            _ir(), _atlas(), plan, enforce_page_composition=False,
        )


def test_model_template_composer_cli_writes_composition(tmp_path: Path) -> None:
    ir_path, atlas_path, plan_path = (
        tmp_path / "ir.json", tmp_path / "atlas.json", tmp_path / "plan.json"
    )
    output = tmp_path / "composition.json"
    ir_path.write_text(json.dumps(_ir()), encoding="utf-8")
    atlas_path.write_text(json.dumps(_atlas()), encoding="utf-8")
    plan_path.write_text(json.dumps(_model_plan()), encoding="utf-8")

    completed = subprocess.run([
        sys.executable, "-m", "engine", "plan-model-template-components",
        "--ir", str(ir_path),
        "--component-atlas", str(atlas_path),
        "--model-plan", str(plan_path),
        "--json-out", str(output),
    ], cwd=ROOT, text=True, capture_output=True, check=False)

    assert completed.returncode == 0, completed.stderr
    assert json.loads(output.read_text())["coverage"]["status"] == "complete"


def test_model_template_composer_builds_new_native_component_when_atlas_has_no_match() -> None:
    ir = _ir()
    intent = ir["slides"][0]["component_intent"]
    intent.update({
        "mode": "model_authored",
        "semantic_use": "causal system",
        "candidate_component_ids": [],
        "selected_component_ids": [],
        "new_component_id": "model.causal-system",
        "style_reference_component_ids": ["template.cards"],
    })
    plan = {
        "schema_version": "1.0.0",
        "slides": [{
            "slide_id": "s1",
            "page_composition": {
                "page_role": "body",
                "recipe": "causal-mechanism",
                "variant": "native-system-with-implication",
                "semantic_layers": ["assertion", "primary_evidence", "implication"],
                "content_modules": [
                    {
                        "module_id": "system",
                        "role": "primary_evidence",
                        "component_ids": ["model.causal-system"],
                        "information_unit_count": 3,
                    },
                    {
                        "module_id": "implication",
                        "role": "implication",
                        "component_ids": ["model.causal-system"],
                        "information_unit_count": 1,
                    },
                ],
                "takeaway": "The system view connects the evidence to the operating implication.",
            },
            "components": [{
                "component_id": "model.causal-system",
                "author_script": "/tmp/causal-system.py",
                "required_binding_names": ["bind:slide:s1:title"],
                "placement": {"x": 0.05, "y": 0.1, "w": 0.9, "h": 0.8},
            }],
        }],
    }

    composition = build_model_template_composition(ir, _atlas(), plan)
    strict_plan = build_component_plan(_atlas(), composition)

    assert composition["component_intent"]["status"] == "pass"
    assert strict_plan["operations"] == [{
        "kind": "model_authored_native_component",
        "destination_slide_index": 11,
        "component_instance_id": "slide-11-component-1",
        "component_id": "model.causal-system",
        "slide_id": "s1",
        "author_script": "/tmp/causal-system.py",
        "required_binding_names": ["bind:slide:s1:title"],
        "asset_bindings": [],
        "author_context": {},
        "placement": {"x": 0.05, "y": 0.1, "w": 0.9, "h": 0.8},
    }]


def test_model_template_composer_allows_authored_support_around_reused_components() -> None:
    ir = _ir()
    ir["slides"][0]["component_intent"]["new_component_id"] = "model.title-strip"
    ir["slides"][0]["component_intent"]["style_reference_component_ids"] = ["template.cards"]
    plan = _model_plan()
    plan["slides"][0]["components"].append({
        "component_id": "model.title-strip",
        "model_authored": True,
        "author_script": "/tmp/title-strip.py",
        "required_binding_names": ["bind:slide:s1:title"],
        "placement": {"x": 0.04, "y": 0.02, "w": 0.92, "h": 0.12},
    })

    composition = build_model_template_composition(ir, _atlas(), plan)
    strict_plan = build_component_plan(_atlas(), composition)

    assert [item["component_id"] for item in composition["pages"][0]["components"]] == [
        "template.cards", "template.metrics", "model.title-strip",
    ]
    assert strict_plan["operations"][-1]["kind"] == "model_authored_native_component"

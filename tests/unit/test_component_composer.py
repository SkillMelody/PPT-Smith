from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from engine.component_composer import build_component_plan


ROOT = Path(__file__).resolve().parents[2]


def _atlas() -> dict:
    return {
        "schema_version": "1.0.0",
        "status": "reviewed",
        "source": {"sha256": "sha256:template"},
        "components": [
            {
                "component_id": "funnel.primary",
                "family": "funnel",
                "slide_index": 26,
                "semantic_uses": ["conversion"],
                "groups": [],
                "parameters": {"element_count": {"minimum": 1, "maximum": 8}},
            },
            {
                "component_id": "timeline.primary",
                "family": "timeline",
                "slide_index": 12,
                "semantic_uses": ["sequence"],
                "groups": [],
                "parameters": {"element_count": {"minimum": 2, "maximum": 6}},
            },
        ],
    }


def _elements(prefix: str, count: int) -> list[dict]:
    return [
        {
            "text": f"{prefix} {index + 1}",
            "value": count - index,
            "binding_name": f"bind:block:page:{prefix}:item:{index}",
        }
        for index in range(count)
    ]


def test_component_composer_builds_multiple_component_operations_from_data_count() -> None:
    composition = {
        "schema_version": "1.0.0",
        "pages": [{
            "destination_slide_index": 4,
            "components": [
                {
                    "semantic_use": "conversion",
                    "elements": _elements("funnel", 4),
                    "placement": {"x": 0.05, "y": 0.18, "w": 0.42, "h": 0.68},
                },
                {
                    "semantic_use": "sequence",
                    "elements": _elements("timeline", 5),
                    "placement": {"x": 0.53, "y": 0.18, "w": 0.42, "h": 0.68},
                },
            ],
        }],
    }

    plan = build_component_plan(_atlas(), composition)

    assert plan["schema_version"] == "1.0.0"
    assert [operation["kind"] for operation in plan["operations"]] == [
        "component_clone", "component_clone",
    ]
    assert plan["operations"][0]["component_requirement"] == {
        "semantic_use": "conversion",
        "element_count": 4,
    }
    assert plan["operations"][1]["component_requirement"] == {
        "semantic_use": "sequence",
        "element_count": 5,
    }
    assert [operation["component_instance_id"] for operation in plan["operations"]] == [
        "slide-4-component-1", "slide-4-component-2",
    ]
    assert [item["component_id"] for item in plan["selections"]] == [
        "funnel.primary", "timeline.primary",
    ]


def test_component_composer_rejects_overlapping_slots_on_the_same_page() -> None:
    composition = {
        "schema_version": "1.0.0",
        "pages": [{
            "destination_slide_index": 4,
            "components": [
                {
                    "semantic_use": "conversion",
                    "elements": _elements("funnel", 4),
                    "placement": {"x": 0.05, "y": 0.18, "w": 0.6, "h": 0.68},
                },
                {
                    "semantic_use": "sequence",
                    "elements": _elements("timeline", 5),
                    "placement": {"x": 0.5, "y": 0.18, "w": 0.45, "h": 0.68},
                },
            ],
        }],
    }

    with pytest.raises(ValueError, match="overlap"):
        build_component_plan(_atlas(), composition)


def test_component_composer_refuses_to_force_data_over_component_capacity() -> None:
    composition = {
        "schema_version": "1.0.0",
        "pages": [{
            "destination_slide_index": 4,
            "components": [{
                "semantic_use": "conversion",
                "elements": _elements("funnel", 9),
                "placement": {"x": 0.05, "y": 0.18, "w": 0.9, "h": 0.68},
            }],
        }],
    }

    with pytest.raises(ValueError, match="no reviewed component"):
        build_component_plan(_atlas(), composition)


def test_component_composer_cli_writes_a_strict_multi_component_plan(tmp_path: Path) -> None:
    atlas_path = tmp_path / "atlas.json"
    composition_path = tmp_path / "composition.json"
    output_path = tmp_path / "strict-plan.json"
    atlas_path.write_text(json.dumps(_atlas()), encoding="utf-8")
    composition_path.write_text(json.dumps({
        "schema_version": "1.0.0",
        "pages": [{
            "destination_slide_index": 4,
            "components": [{
                "semantic_use": "conversion",
                "elements": _elements("funnel", 4),
                "placement": {"x": 0.05, "y": 0.18, "w": 0.42, "h": 0.68},
            }],
        }],
    }), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable, "-m", "engine", "compose-components",
            "--component-atlas", str(atlas_path),
            "--composition", str(composition_path),
            "--json-out", str(output_path),
        ],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )

    assert completed.returncode == 0, completed.stderr
    plan = json.loads(output_path.read_text(encoding="utf-8"))
    assert plan["operations"][0]["kind"] == "component_clone"
    assert plan["selections"][0]["component_id"] == "funnel.primary"


def test_component_composer_expands_a_composite_into_independent_ring_operations() -> None:
    atlas = {
        "schema_version": "1.0.0", "status": "reviewed",
        "source": {"sha256": "sha256:template"},
        "components": [{
            "component_id": "ring.metric", "family": "metric_ring", "granularity": "micro",
            "slide_index": 16, "semantic_uses": ["proportion metric"],
            "groups": [{"role": "chart", "members": [{"shape_name": "ring-chart", "kind": "chart"}]}],
            "parameters": {"element_count": {"minimum": 1, "maximum": 1}},
        }, {
            "component_id": "ring.comparison", "family": "ring_comparison", "granularity": "composite",
            "slide_index": 16, "semantic_uses": ["before after comparison"], "groups": [],
            "children": [{
                "slot_id": "before", "component_id": "ring.metric",
                "placement": {"x": 0.0, "y": 0.0, "w": 0.45, "h": 1.0},
            }, {
                "slot_id": "after", "component_id": "ring.metric",
                "placement": {"x": 0.55, "y": 0.0, "w": 0.45, "h": 1.0},
            }],
            "parameters": {"element_count": {"minimum": 2, "maximum": 2}},
        }],
    }
    composition = {
        "schema_version": "1.0.0",
        "pages": [{
            "destination_slide_index": 4,
            "components": [{
                "semantic_use": "before after comparison", "family": "ring_comparison",
                "element_count": 2,
                "placement": {"x": 0.1, "y": 0.2, "w": 0.8, "h": 0.5},
                "children": {
                    "before": {
                        "semantic_use": "proportion metric",
                        "chart": {"binding_name": "bind:chart:impact:before", "data": {"categories": ["Share", "Other"], "series": [{"name": "Share", "values": [45, 55]}]}},
                        "text_bindings": [],
                    },
                    "after": {
                        "semantic_use": "proportion metric",
                        "chart": {"binding_name": "bind:chart:impact:after", "data": {"categories": ["Share", "Other"], "series": [{"name": "Share", "values": [64, 36]}]}},
                        "text_bindings": [],
                    },
                },
            }],
        }],
    }

    plan = build_component_plan(atlas, composition)

    assert [operation["kind"] for operation in plan["operations"]] == [
        "chart_component_clone", "chart_component_clone",
    ]
    assert [operation["component_instance_id"] for operation in plan["operations"]] == [
        "slide-4-component-1-before", "slide-4-component-1-after",
    ]
    assert plan["operations"][0]["placement"] == {"x": 0.1, "y": 0.2, "w": 0.36, "h": 0.5}
    assert plan["operations"][1]["placement"] == {"x": 0.54, "y": 0.2, "w": 0.36, "h": 0.5}
    assert plan["operations"][0]["component_requirement"]["component_id"] == "ring.metric"
    assert [item["component_id"] for item in plan["selections"]] == [
        "ring.comparison", "ring.metric", "ring.metric",
    ]


def test_component_composer_emits_a_dashboard_clone_for_a_multi_chart_page_recipe() -> None:
    atlas = {
        "schema_version": "1.0.0", "status": "reviewed",
        "source": {"sha256": "sha256:template"},
        "components": [{
            "component_id": "dashboard.research-impact",
            "family": "chart_dashboard",
            "granularity": "page_recipe",
            "slide_index": 16,
            "semantic_uses": ["research impact evidence"],
            "groups": [{
                "role": "chart",
                "members": [
                    {"shape_name": "innovation-chart", "kind": "chart"},
                    {"shape_name": "ebit-chart", "kind": "chart"},
                ],
            }, {
                "role": "text",
                "members": [{"shape_name": "dashboard-title", "kind": "text"}],
            }],
            "parameters": {"element_count": {"minimum": 2, "maximum": 2}},
        }],
    }
    charts = [{
        "id": chart_id,
        "binding_name": f"bind:chart:impact:{chart_id}",
        "data": {
            "categories": ["Reported", "Other"],
            "series": [{"name": "Share", "values": values}],
        },
    } for chart_id, values in (("innovation", [64, 36]), ("ebit", [39, 61]))]
    composition = {
        "schema_version": "1.0.0",
        "pages": [{
            "destination_slide_index": 48,
            "components": [{
                "semantic_use": "research impact evidence",
                "family": "chart_dashboard",
                "element_count": 2,
                "charts": charts,
                "text_bindings": [],
                "clear_text_names": ["dashboard-title"],
                "placement": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
            }],
        }],
    }

    plan = build_component_plan(atlas, composition)

    assert plan["operations"] == [{
        "kind": "chart_dashboard_clone",
        "destination_slide_index": 48,
        "component_instance_id": "slide-48-component-1",
        "component_requirement": {
            "semantic_use": "research impact evidence",
            "element_count": 2,
            "family": "chart_dashboard",
        },
        "charts": charts,
        "text_bindings": [],
        "clear_text_names": ["dashboard-title"],
        "placement": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
    }]


def test_component_composer_emits_a_reviewed_fixed_native_group_without_shape_names() -> None:
    atlas = {
        "schema_version": "1.0.0", "status": "reviewed",
        "source": {"sha256": "sha256:template"},
        "components": [{
            "component_id": "insight.list",
            "family": "fixed_native_group",
            "granularity": "section",
            "renderer": "native_group",
            "slide_index": 16,
            "semantic_uses": ["evidence insight list"],
            "groups": [{
                "role": "label", "bind_field": "title",
                "members": [{"shape_name": "group-title", "kind": "text"}],
            }, {
                "role": "label", "bind_field": "detail",
                "members": [
                    {"shape_name": "group-detail-1", "kind": "text"},
                    {"shape_name": "group-detail-2", "kind": "text"},
                ],
            }, {
                "role": "decoration",
                "members": [{"shape_name": "group-background", "kind": "shape"}],
            }],
            "parameters": {"element_count": {"minimum": 2, "maximum": 2}},
        }],
    }
    component = {
        "component_id": "insight.list",
        "semantic_use": "evidence insight list",
        "family": "fixed_native_group",
        "element_count": 2,
        "placement": {"x": 0.1, "y": 0.2, "w": 0.8, "h": 0.5},
        "text_bindings": [{
            "field": "title",
            "binding_name": "bind:block:impact:insights:item:0",
            "text": "Management implications",
        }, {
            "field": "detail",
            "binding_name": "bind:block:impact:insights:item:1",
            "text": "Innovation impact is broader than EBIT impact.",
        }, {
            "field": "detail",
            "binding_name": "bind:block:impact:insights:item:2",
            "text": "Workflow redesign remains the scaling constraint.",
        }],
    }
    composition = {
        "schema_version": "1.0.0",
        "pages": [{"destination_slide_index": 38, "components": [component]}],
    }

    plan = build_component_plan(atlas, composition)

    assert plan["operations"] == [{
        "kind": "native_group_component_clone",
        "destination_slide_index": 38,
        "component_instance_id": "slide-38-component-1",
        "component_requirement": {
            "semantic_use": "evidence insight list",
            "element_count": 2,
            "family": "fixed_native_group",
            "component_id": "insight.list",
        },
        "text_bindings": component["text_bindings"],
        "placement": {"x": 0.1, "y": 0.2, "w": 0.8, "h": 0.5},
    }]
    assert "shape_names" not in plan["operations"][0]

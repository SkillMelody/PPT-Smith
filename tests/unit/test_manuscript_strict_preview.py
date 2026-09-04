from __future__ import annotations

from types import SimpleNamespace

from engine.manuscript_strict_preview import (
    build_manuscript_strict_preview_bundle,
    expected_component_element_count,
    rendered_component_element_count,
)


def test_preview_bundle_builds_ir_titles_components_and_honest_placeholders() -> None:
    content_bindings = {"slides": [{
        "id": "planned",
        "title": "已覆盖页",
        "items": ["发现 A", "发现 B"],
    }, {
        "id": "unsupported",
        "title": "待补组件页",
        "items": ["证据 A"],
    }]}
    storyboard = {"slides": [{"purpose": "planned"}, {"purpose": "unsupported"}]}
    composition = {
        "source_page_count": 2,
        "template_slide_count": 37,
        "pages": [{
            "output_page_index": 1,
            "purpose": "planned",
            "destination_slide_index": 38,
            "components": [],
        }],
        "unsupported_pages": [{
            "output_page_index": 2,
            "purpose": "unsupported",
            "layout_pattern": "cycle relationship",
            "reason_code": "no_component_route",
            "reason": "no reviewed component route",
        }],
    }
    component_plan = {"operations": [{
        "kind": "component_clone",
        "destination_slide_index": 38,
        "component_requirement": {
            "semantic_use": "capability cards",
            "family": "card_grid",
            "element_count": 2,
        },
        "elements": [{
            "value": None,
            "labels": {
                "title": {
                    "text": "市场信号",
                    "binding_name": "bind:block:planned:component_items:item:0",
                },
                "detail": {
                    "text": "发现 A",
                    "binding_name": "bind:block:planned:component_items:detail:0",
                },
            },
        }, {
            "value": 2,
            "labels": {
                "badge": {
                    "text": "2",
                    "binding_name": "bind:block:planned:component_badges:item:1",
                },
                "title": {
                    "text": "客户反馈",
                    "binding_name": "bind:block:planned:component_items:item:1",
                },
                "detail": {
                    "text": "发现 B",
                    "binding_name": "bind:block:planned:component_items:detail:1",
                },
            },
        }],
    }]}

    bundle = build_manuscript_strict_preview_bundle(
        content_bindings=content_bindings,
        storyboard=storyboard,
        composition=composition,
        component_plan=component_plan,
    )

    assert bundle["summary"] == {
        "output_pages": 2,
        "component_operations": 1,
        "title_operations": 2,
        "placeholder_operations": 1,
        "total_operations": 4,
        "evidence_units": 0,
        "source_references": 0,
    }
    slides = {slide["id"]: slide for slide in bundle["ir"]["slides"]}
    assert slides["planned"]["title"] == "已覆盖页"
    blocks = {block["id"]: block for block in slides["planned"]["blocks"]}
    assert blocks["component_items"]["items"] == [
        {"text": "市场信号", "detail": "发现 A"},
        {"text": "客户反馈", "detail": "发现 B"},
    ]
    assert blocks["component_badges"]["items"][1]["text"] == "2"
    unsupported = {block["id"]: block for block in slides["unsupported"]["blocks"]}
    assert unsupported["unsupported_status"]["items"][0]["text"] == "组件待补充"
    assert "暂无 reviewed 组件" in unsupported["unsupported_status"]["items"][0]["detail"]
    operations = bundle["strict_plan"]["operations"]
    assert [operation["destination_slide_index"] for operation in operations if operation["kind"] == "native_group_clone"] == [38, 39, 39]
    assert len([operation for operation in operations if operation["kind"] == "component_clone"]) == 1


def test_preview_bundle_supports_legacy_component_item_bindings() -> None:
    bundle = build_manuscript_strict_preview_bundle(
        content_bindings={"slides": [{"id": "legacy", "title": "旧组件", "items": ["行动"]}]},
        storyboard={"slides": [{"purpose": "legacy"}]},
        composition={
            "source_page_count": 1,
            "template_slide_count": 37,
            "pages": [{"output_page_index": 1, "purpose": "legacy", "destination_slide_index": 38}],
            "unsupported_pages": [],
        },
        component_plan={"operations": [{
            "kind": "component_clone",
            "destination_slide_index": 38,
            "component_requirement": {"semantic_use": "prioritization", "element_count": 1},
            "elements": [{
                "text": "行动",
                "binding_name": "bind:block:legacy:component_items:item:0",
            }],
        }]},
    )

    slide = bundle["ir"]["slides"][0]
    assert slide["blocks"][0]["items"] == [{"text": "行动"}]


def test_preview_bundle_carries_dashboard_charts_and_text_bindings_into_ir() -> None:
    charts = [{
        "id": "innovation",
        "binding_name": "bind:chart:innovation_impact:innovation",
        "data": {
            "categories": ["促进", "其他"],
            "series": [{"name": "受访者占比", "values": [64, 36]}],
        },
    }]
    operation = {
        "kind": "chart_dashboard_clone",
        "destination_slide_index": 38,
        "component_requirement": {
            "semantic_use": "research impact evidence",
            "family": "chart_dashboard",
            "element_count": 1,
        },
        "charts": charts,
        "text_bindings": [{
            "shape_name": "dashboard-value",
            "binding_name": "bind:block:innovation_impact:dashboard_values:item:0",
            "text": "64%",
        }],
        "clear_text_names": ["dashboard-title"],
        "placement": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
    }

    bundle = build_manuscript_strict_preview_bundle(
        content_bindings={"slides": [{
            "id": "innovation_impact",
            "title": "AI 影响：创新领先",
        }]},
        storyboard={"slides": [{"purpose": "innovation_impact"}]},
        composition={
            "source_page_count": 1,
            "template_slide_count": 37,
            "pages": [{
                "output_page_index": 1,
                "purpose": "innovation_impact",
                "destination_slide_index": 38,
            }],
            "unsupported_pages": [],
        },
        component_plan={"operations": [operation]},
    )

    slide = bundle["ir"]["slides"][0]
    assert slide["charts"] == [{"id": "innovation", "data": charts[0]["data"]}]
    assert slide["blocks"] == [{
        "id": "dashboard_values",
        "role": "list",
        "items": [{"text": "64%"}],
    }]
    assert operation in bundle["strict_plan"]["operations"]


def test_preview_bundle_carries_recursive_chart_and_native_group_components_into_ir() -> None:
    chart_operation = {
        "kind": "chart_component_clone",
        "destination_slide_index": 38,
        "component_instance_id": "impact-kpi",
        "component_requirement": {
            "semantic_use": "single KPI comparison",
            "family": "kpi_chart_card",
            "element_count": 1,
        },
        "chart": {
            "id": "innovation",
            "binding_name": "bind:chart:innovation_impact:innovation",
            "data": {
                "categories": ["促进", "其他"],
                "series": [{"name": "受访者占比", "values": [64, 36]}],
            },
        },
        "text_bindings": [{
            "field": "metric",
            "binding_name": "bind:block:innovation_impact:dashboard_values:item:0",
            "text": "64%",
        }],
    }
    native_group_operation = {
        "kind": "native_group_component_clone",
        "destination_slide_index": 38,
        "component_instance_id": "impact-summary",
        "component_requirement": {
            "semantic_use": "four-part impact summary",
            "family": "fixed_native_group",
            "element_count": 4,
        },
        "text_bindings": [{
            "field": "item",
            "binding_name": f"bind:block:innovation_impact:impact_summary:item:{index}",
            "text": text,
        } for index, text in enumerate(["创新", "体验", "差异", "利润"])],
    }

    bundle = build_manuscript_strict_preview_bundle(
        content_bindings={"slides": [{
            "id": "innovation_impact",
            "title": "AI 影响：创新领先",
        }]},
        storyboard={"slides": [{"purpose": "innovation_impact"}]},
        composition={
            "source_page_count": 1,
            "template_slide_count": 37,
            "pages": [{
                "output_page_index": 1,
                "purpose": "innovation_impact",
                "destination_slide_index": 38,
            }],
            "unsupported_pages": [],
        },
        component_plan={"operations": [chart_operation, native_group_operation]},
    )

    slide = bundle["ir"]["slides"][0]
    assert slide["charts"] == [{
        "id": "innovation",
        "data": chart_operation["chart"]["data"],
    }]
    blocks = {block["id"]: block for block in slide["blocks"]}
    assert blocks["dashboard_values"]["items"] == [{"text": "64%"}]
    assert blocks["impact_summary"]["items"] == [
        {"text": "创新"}, {"text": "体验"}, {"text": "差异"}, {"text": "利润"},
    ]
    assert bundle["summary"]["component_operations"] == 2


def test_recursive_component_counts_use_semantic_elements_and_bound_native_objects() -> None:
    chart_operation = {
        "kind": "chart_component_clone",
        "component_requirement": {"element_count": 1},
        "chart": {"binding_name": "bind:chart:impact:kpi"},
        "text_bindings": [{"binding_name": "bind:block:impact:kpi:item:0", "text": "64%"}],
    }
    native_group_operation = {
        "kind": "native_group_component_clone",
        "component_requirement": {"element_count": 4},
        "text_bindings": [
            {"binding_name": f"bind:block:impact:summary:item:{index}", "text": text}
            for index, text in enumerate(["A", "B", "C", "D"])
        ],
    }
    shapes = [
        SimpleNamespace(name="bind:chart:impact:kpi", has_chart=True),
        SimpleNamespace(name="bind:block:impact:kpi:item:0", has_chart=False),
        *[
            SimpleNamespace(
                name=f"bind:block:impact:summary:item:{index}", has_chart=False,
            )
            for index in range(4)
        ],
    ]

    assert expected_component_element_count(chart_operation) == 1
    assert expected_component_element_count(native_group_operation) == 4
    assert rendered_component_element_count(chart_operation, shapes) == 1
    assert rendered_component_element_count(native_group_operation, shapes) == 4


def test_preview_bundle_preserves_item_source_refs_and_evidence_counts() -> None:
    operation = {
        "kind": "component_clone",
        "destination_slide_index": 38,
        "component_requirement": {
            "semantic_use": "capability cards",
            "family": "card_grid",
            "element_count": 1,
        },
        "elements": [{
            "value": None,
            "labels": {
                "title": {
                    "text": "Revenue increased",
                    "binding_name": "bind:block:growth:component_items:item:0",
                    "source_ref": {"source_id": "src", "loc": "para_1"},
                    "source_refs": [
                        {"source_id": "src", "loc": "para_1"},
                        {"source_id": "src", "loc": "para_2"},
                    ],
                    "evidence_id": "src:para_1",
                },
                "detail": {
                    "text": "Revenue increased 36%",
                    "binding_name": "bind:block:growth:component_items:detail:0",
                    "source_ref": {"source_id": "src", "loc": "para_1"},
                    "evidence_id": "src:para_1",
                },
            },
        }],
    }
    bundle = build_manuscript_strict_preview_bundle(
        content_bindings={"slides": [{
            "id": "growth",
            "title": "Revenue increased",
            "items": ["Revenue increased 36%"],
        }]},
        storyboard={"slides": [{"purpose": "growth"}]},
        composition={
            "source_page_count": 1,
            "template_slide_count": 37,
            "pages": [{
                "output_page_index": 1,
                "purpose": "growth",
                "destination_slide_index": 38,
            }],
            "unsupported_pages": [],
        },
        component_plan={"operations": [operation]},
    )

    item = bundle["ir"]["slides"][0]["blocks"][0]["items"][0]
    assert item["source_ref"] == {"source_id": "src", "loc": "para_1"}
    assert item["source_refs"] == [
        {"source_id": "src", "loc": "para_1"},
        {"source_id": "src", "loc": "para_2"},
    ]
    assert item["evidence_id"] == "src:para_1"
    assert bundle["summary"]["evidence_units"] == 1
    assert bundle["summary"]["source_references"] == 2

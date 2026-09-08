from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from engine.component_atlas import (
    build_component_atlas,
    resolve_chart_dashboard_binding,
    resolve_chart_component_binding,
    resolve_component_binding,
    resolve_native_group_binding,
    select_component,
)
from engine.component_composer import build_component_plan
from engine.component_inventory import build_template_component_inventory
from engine.manuscript_component_planner import build_manuscript_component_composition


ROOT = Path(__file__).resolve().parents[2]
_HISTORICAL_PROJECT = ROOT / "projects" / "state-ai-full-native-template_ppt169_20260828"
_CONFIGURED_PROJECT = os.environ.get("PPT_SMITH_MCKINSEY_FIXTURE")
_PROJECT_CANDIDATE = (
    Path(_CONFIGURED_PROJECT).expanduser()
    if _CONFIGURED_PROJECT
    else _HISTORICAL_PROJECT
)
PROJECT = _PROJECT_CANDIDATE if _PROJECT_CANDIDATE.is_dir() else None

pytestmark = pytest.mark.skipif(
    PROJECT is None,
    reason="McKinsey reference fixture not installed",
)


def test_real_mckinsey_pyramid_is_reviewed_for_three_and_five_levels() -> None:
    template = PROJECT / "sources" / "麦肯锡风格.pptx"
    review = json.loads(
        (PROJECT / "analysis" / "component-review.v1.json").read_text(encoding="utf-8")
    )

    atlas = build_component_atlas(template, review)
    three = resolve_component_binding(atlas, {
        "semantic_use": "hierarchy",
        "element_count": 3,
        "family": "pyramid",
    })
    five = resolve_component_binding(atlas, {
        "semantic_use": "hierarchy",
        "element_count": 5,
        "family": "pyramid",
    })

    assert three["component_id"] == "mckinsey.pyramid.project-management-3d"
    assert three["binding_schema_version"] == "2.0.0"
    assert [len(item["segment_names"]) for item in three["item_groups"]] == [3, 3, 2]
    assert all(set(item["label_fields"]) == {"title"} for item in three["item_groups"])
    assert three["shared_names"] == ["直接连接符 167", "直接连接符 170"]
    assert five["component_id"] == three["component_id"]


def test_real_mckinsey_information_cards_are_reviewed_for_three_and_five_items() -> None:
    template = PROJECT / "sources" / "麦肯锡风格.pptx"
    review = json.loads(
        (PROJECT / "analysis" / "component-review.v1.json").read_text(encoding="utf-8")
    )

    atlas = build_component_atlas(template, review)
    three = resolve_component_binding(atlas, {
        "semantic_use": "key initiatives",
        "element_count": 3,
        "family": "card_grid",
    })
    five = resolve_component_binding(atlas, {
        "semantic_use": "key initiatives",
        "element_count": 5,
        "family": "card_grid",
    })

    assert three["component_id"] == "mckinsey.cards.project-actions"
    assert three["binding_schema_version"] == "2.0.0"
    assert len(three["item_groups"]) == 11
    assert all(len(item["segment_names"]) == 1 for item in three["item_groups"])
    assert all(set(item["label_fields"]) == {"title", "detail"} for item in three["item_groups"])
    assert three["shared_names"] == ["矩形 161", "矩形 162", "矩形 163"]
    assert five["component_id"] == three["component_id"]


def test_real_mckinsey_transformation_timeline_is_reviewed_for_three_and_five_stages() -> None:
    template = PROJECT / "sources" / "麦肯锡风格.pptx"
    review = json.loads(
        (PROJECT / "analysis" / "component-review.v1.json").read_text(encoding="utf-8")
    )

    atlas = build_component_atlas(template, review)
    three = resolve_component_binding(atlas, {
        "semantic_use": "transformation roadmap",
        "element_count": 3,
        "family": "timeline",
    })
    five = resolve_component_binding(atlas, {
        "semantic_use": "transformation roadmap",
        "element_count": 5,
        "family": "timeline",
    })

    assert three["component_id"] == "mckinsey.timeline.digital-transformation"
    assert three["binding_schema_version"] == "2.0.0"
    assert len(three["item_groups"]) == 5
    assert all(len(item["segment_names"]) == 4 for item in three["item_groups"])
    assert all(
        all(not name.startswith("组合 ") for name in item["segment_names"])
        for item in three["item_groups"]
    )
    assert all(
        set(item["label_fields"]) == {
            "badge", "title", "detail", "metric_label", "metric_value",
        }
        for item in three["item_groups"]
    )
    assert three["shared_names"] == []
    assert five["component_id"] == three["component_id"]


def test_real_mckinsey_icon_capability_cards_are_reviewed_for_three_and_five_items() -> None:
    template = PROJECT / "sources" / "麦肯锡风格.pptx"
    review = json.loads(
        (PROJECT / "analysis" / "component-review.v1.json").read_text(encoding="utf-8")
    )

    atlas = build_component_atlas(template, review)
    three = resolve_component_binding(atlas, {
        "semantic_use": "icon capability cards",
        "element_count": 3,
        "family": "icon_card_grid",
    })
    five = resolve_component_binding(atlas, {
        "semantic_use": "icon capability cards",
        "element_count": 5,
        "family": "icon_card_grid",
    })

    assert three["component_id"] == "mckinsey.cards.icon-capabilities"
    assert three["binding_schema_version"] == "2.0.0"
    assert len(three["item_groups"]) == 5
    assert all(len(item["segment_names"]) == 3 for item in three["item_groups"])
    assert all(
        any(name.startswith("Google Shape;") for name in item["segment_names"])
        for item in three["item_groups"]
    )
    assert all(set(item["label_fields"]) == {"title", "detail"} for item in three["item_groups"])
    assert three["shared_names"] == []
    assert five["component_id"] == three["component_id"]


def test_real_mckinsey_dashboard_exposes_single_ring_and_dual_ring_composition() -> None:
    template = PROJECT / "sources" / "麦肯锡风格.pptx"
    review = json.loads(
        (PROJECT / "analysis" / "component-review.v1.json").read_text(encoding="utf-8")
    )

    atlas = build_component_atlas(template, review)
    ring = resolve_chart_component_binding(atlas, {
        "component_id": "mckinsey.ring.proportion",
        "semantic_use": "proportion metric",
        "family": "metric_ring",
        "element_count": 1,
    })
    bridge = resolve_component_binding(atlas, {
        "component_id": "mckinsey.relation.improvement-bridge",
        "semantic_use": "comparison relation",
        "family": "comparison_bridge",
        "element_count": 1,
    })
    comparison_selection = select_component(atlas, {
        "component_id": "mckinsey.ring-comparison.two-way",
        "semantic_use": "before after comparison",
        "family": "ring_comparison",
        "element_count": 2,
    })
    comparison = next(
        item for item in atlas["components"]
        if item["component_id"] == comparison_selection["component_id"]
    )

    assert ring["chart_names"] == ["图表 13"]
    assert ring["label_fields"] == {"value": ["文本框 14"], "label": ["文本框 23"]}
    assert ring["decoration_names"] == ["箭头: 上 15"]
    assert bridge["item_groups"] == [{
        "segment_names": ["梯形 32", "梯形 33"],
        "label_fields": {"text": ["文本框 31"]},
    }]
    assert bridge["layout_mode"] == "fixed_cluster"
    assert [child["component_id"] for child in comparison["children"]] == [
        "mckinsey.ring.proportion",
        "mckinsey.relation.improvement-bridge",
        "mckinsey.ring.proportion",
    ]


def test_real_mckinsey_dashboard_exposes_the_impact_bar_as_a_micro_component() -> None:
    template = PROJECT / "sources" / "麦肯锡风格.pptx"
    review = json.loads(
        (PROJECT / "analysis" / "component-review.v1.json").read_text(encoding="utf-8")
    )

    atlas = build_component_atlas(template, review)
    impact = resolve_chart_component_binding(atlas, {
        "component_id": "mckinsey.impact-bar.business-outcome",
        "semantic_use": "impact gap evidence",
        "family": "impact_bar",
        "element_count": 1,
    })

    assert impact["chart_names"] == ["图表 134"]
    assert impact["label_fields"] == {
        "title": ["文本框 35"],
        "positive_label": ["文本框 36"],
        "positive_detail": ["文本框 37"],
        "gap_label": ["文本框 38"],
        "gap_detail": ["文本框 39"],
    }
    assert impact["decoration_names"] == []


def test_real_mckinsey_research_dashboard_preserves_its_internal_visual_scaffolding() -> None:
    template = PROJECT / "sources" / "麦肯锡风格.pptx"
    review = json.loads(
        (PROJECT / "analysis" / "component-review.v1.json").read_text(encoding="utf-8")
    )

    atlas = build_component_atlas(template, review)
    dashboard = resolve_chart_dashboard_binding(atlas, {
        "component_id": "mckinsey.dashboard.research-impact",
        "semantic_use": "research impact evidence",
        "family": "chart_dashboard",
        "element_count": 7,
    })

    assert dashboard["decoration_names"] == [
        "直线连接符 11",
        "矩形: 圆顶角 28",
        "矩形: 圆角 1",
        "矩形: 圆角 4",
        "矩形: 圆角 24",
        "矩形: 圆角 25",
        "矩形: 圆角 30",
        "箭头: 上 15",
        "箭头: 上 22",
        "梯形 32",
        "梯形 33",
        "直接连接符 5",
        "直接连接符 6",
        "直接连接符 9",
        "直接连接符 11",
    ]


def test_real_mckinsey_research_dashboard_orders_ebit_data_for_the_native_reversed_bar_axis() -> None:
    bindings = json.loads(
        (PROJECT / "analysis" / "content-bindings.v1.json").read_text(encoding="utf-8")
    )
    impact = next(slide for slide in bindings["slides"] if slide["id"] == "innovation_impact")
    ebit = next(chart for chart in impact["dashboard"]["charts"] if chart["id"] == "enterprise_ebit")
    text = {
        item["shape_name"]: item["text"]
        for item in impact["dashboard"]["text_bindings"]
    }

    assert ebit["data"] == {
        "categories": ["未报告企业级 EBIT 影响", "已报告企业级 EBIT 影响"],
        "series": [{"name": "受访者占比", "values": [61, 39]}],
    }
    assert text["文本框 37"] == "39% 企业级 EBIT 影响"
    assert text["文本框 38"] == "未报告："
    assert text["文本框 39"] == "61% 尚未体现企业级 EBIT 影响"


def test_real_mckinsey_dashboard_exposes_a_reusable_kpi_card_and_four_card_composite() -> None:
    template = PROJECT / "sources" / "麦肯锡风格.pptx"
    review = json.loads(
        (PROJECT / "analysis" / "component-review.v1.json").read_text(encoding="utf-8")
    )
    atlas = build_component_atlas(template, review)

    card = resolve_chart_component_binding(atlas, {
        "component_id": "mckinsey.kpi-chart-card.metric-comparison",
        "semantic_use": "single KPI comparison",
        "family": "kpi_chart_card",
        "element_count": 1,
    })
    assert card["chart_names"] == ["图表 51"]
    assert card["label_fields"] == {
        "title": ["文本框 53"],
        "metric": ["文本框 56"],
    }
    assert card["decoration_names"] == ["矩形: 圆角 7", "矩形: 圆角 54"]
    trend = resolve_chart_component_binding(atlas, {
        "component_id": "mckinsey.kpi-chart-card.metric-trend",
        "semantic_use": "single KPI trend",
        "family": "kpi_chart_card",
        "element_count": 1,
    })
    assert trend["chart_names"] == ["图表 104"]
    assert trend["label_fields"] == {
        "title": ["文本框 107"],
        "metric": ["文本框 108"],
    }
    assert trend["decoration_names"] == ["矩形: 圆角 103", "矩形: 圆角 105"]

    chart_payload = lambda suffix, values: {
        "chart": {
            "binding_name": f"bind:chart:impact:{suffix}",
            "data": {
                "categories": ["Primary", "Other"],
                "series": [{"name": "Share", "values": values}],
            },
        },
        "text_bindings": [{
            "field": "title",
            "binding_name": f"bind:block:impact:kpis:title:{suffix}",
            "text": suffix.replace("_", " ").title(),
        }, {
            "field": "metric",
            "binding_name": f"bind:block:impact:kpis:metric:{suffix}",
            "text": f"{values[0]}%",
        }],
    }
    composition = {
        "schema_version": "1.0.0",
        "pages": [{
            "destination_slide_index": 38,
            "components": [{
                "component_id": "mckinsey.kpi-chart-row.four-metrics",
                "semantic_use": "four KPI comparison row",
                "family": "kpi_chart_row",
                "element_count": 4,
                "placement": {"x": 0.05, "y": 0.15, "w": 0.9, "h": 0.4},
                "children": {
                    "metric_1": chart_payload("innovation", [64, 36]),
                    "metric_2": chart_payload("employee", [45, 55]),
                    "metric_3": chart_payload("customer", [45, 55]),
                    "metric_4": chart_payload("differentiation", [45, 55]),
                },
            }],
        }],
    }

    plan = build_component_plan(atlas, composition)

    assert [operation["kind"] for operation in plan["operations"]] == [
        "chart_component_clone",
        "chart_component_clone",
        "chart_component_clone",
        "chart_component_clone",
    ]
    assert [selection["component_id"] for selection in plan["selections"]] == [
        "mckinsey.kpi-chart-row.four-metrics",
        "mckinsey.kpi-chart-card.metric-comparison",
        "mckinsey.kpi-chart-card.metric-comparison",
        "mckinsey.kpi-chart-card.metric-comparison",
        "mckinsey.kpi-chart-card.metric-trend",
    ]
    assert [round(operation["placement"]["x"], 4) for operation in plan["operations"]] == [
        0.05, 0.275, 0.5, 0.725,
    ]


def test_real_mckinsey_dashboard_exposes_insight_list_and_quadrant_summary_sections() -> None:
    template = PROJECT / "sources" / "麦肯锡风格.pptx"
    review = json.loads(
        (PROJECT / "analysis" / "component-review.v1.json").read_text(encoding="utf-8")
    )
    atlas = build_component_atlas(template, review)

    insights = resolve_native_group_binding(atlas, {
        "component_id": "mckinsey.insight-list.management-evidence",
        "semantic_use": "management evidence list",
        "family": "fixed_native_group",
        "element_count": 2,
    })
    assert insights["label_fields"] == {
        "title": ["文本框 40"],
        "detail": ["文本框 45", "文本框 46"],
    }
    assert insights["decoration_names"] == [
        "矩形: 圆角 30", "直接连接符 5", "直接连接符 6",
    ]

    quadrant = resolve_native_group_binding(atlas, {
        "component_id": "mckinsey.quadrant-summary.impact-sequence",
        "semantic_use": "four-part impact summary",
        "family": "fixed_native_group",
        "element_count": 4,
    })
    assert quadrant["label_fields"] == {
        "item": ["文本框 41", "文本框 42", "文本框 43", "文本框 44"],
    }
    assert quadrant["decoration_names"] == [
        "矩形: 圆角 1", "直接连接符 9", "直接连接符 11",
    ]
    outcome_shell = resolve_native_group_binding(atlas, {
        "component_id": "mckinsey.outcome-shell.business-results",
        "semantic_use": "business outcome evidence shell",
        "family": "fixed_native_group",
        "element_count": 1,
    })
    assert outcome_shell["label_fields"] == {"title": ["文本框 3"]}
    assert outcome_shell["decoration_names"] == ["矩形: 圆角 24"]
    outcome_section = select_component(atlas, {
        "component_id": "mckinsey.ring-evidence.business-outcomes",
        "semantic_use": "business outcome ring evidence",
        "family": "ring_evidence_section",
        "element_count": 2,
    })
    assert outcome_section["status"] == "selected"
    component = next(
        item for item in atlas["components"]
        if item["component_id"] == outcome_section["component_id"]
    )
    assert [child["component_id"] for child in component["children"]] == [
        "mckinsey.outcome-shell.business-results",
        "mckinsey.ring-comparison.two-way",
    ]


def test_real_mckinsey_page_16_counts_equivalent_kpi_and_ring_instances_without_alias_components() -> None:
    template = PROJECT / "sources" / "麦肯锡风格.pptx"
    review = json.loads(
        (PROJECT / "analysis" / "component-review.v1.json").read_text(encoding="utf-8")
    )
    atlas = build_component_atlas(template, review)
    comparison = next(
        component for component in atlas["components"]
        if component["component_id"] == "mckinsey.kpi-chart-card.metric-comparison"
    )
    ring = next(
        component for component in atlas["components"]
        if component["component_id"] == "mckinsey.ring.proportion"
    )

    assert [item["instance_id"] for item in comparison["source_instances"]] == [
        "brand-exposure-card", "user-interaction-card",
    ]
    assert [item["instance_id"] for item in ring["source_instances"]] == [
        "secondary-platform-ring",
    ]
    assert len(atlas["components"]) == 24

    inventory = build_template_component_inventory(template, atlas)
    slide = next(item for item in inventory["slides"] if item["slide_index"] == 16)
    assert slide["covered_content_count"] == 52
    assert slide["uncovered_content_count"] == 5
    assert slide["page_recipe_only_content_count"] == 1


def test_real_manuscript_uses_reviewed_dashboard_without_brand_specific_decomposition() -> None:
    template = PROJECT / "sources" / "麦肯锡风格.pptx"
    analysis = PROJECT / "analysis"
    review = json.loads((analysis / "component-review.v1.json").read_text(encoding="utf-8"))
    bindings = json.loads((analysis / "content-bindings.v1.json").read_text(encoding="utf-8"))
    storyboard = json.loads((analysis / "composition-plan.json").read_text(encoding="utf-8"))
    atlas = build_component_atlas(template, review)

    composition = build_manuscript_component_composition(atlas, bindings, storyboard)
    impact = next(page for page in composition["pages"] if page["purpose"] == "innovation_impact")

    assert len(impact["components"]) == 1
    assert impact["components"][0]["family"] == "chart_dashboard"
    assert impact["components"][0]["component_id"] == "mckinsey.dashboard.research-impact"
    plan = build_component_plan(atlas, {"schema_version": "1.0.0", "pages": [impact]})
    assert len(plan["operations"]) == 1
    assert plan["operations"][0]["kind"] == "chart_dashboard_clone"


def test_real_mckinsey_atlas_exposes_distinct_cover_chapter_and_closing_contracts() -> None:
    template = PROJECT / "sources" / "麦肯锡风格.pptx"
    review = json.loads(
        (PROJECT / "analysis" / "component-review.v1.json").read_text(encoding="utf-8")
    )
    atlas = build_component_atlas(template, review)

    cover = resolve_component_binding(atlas, {
        "semantic_use": "cover keywords",
        "family": "icon_card_grid",
        "element_count": 3,
    })
    chapter = resolve_component_binding(atlas, {
        "semantic_use": "chapter insight",
        "family": "dual_panel",
        "element_count": 2,
    })
    closing = resolve_component_binding(atlas, {
        "semantic_use": "closing source note",
        "family": "statement_card",
        "element_count": 1,
    })

    assert cover["component_id"] == "mckinsey.cover.keyword-triad"
    assert cover["binding_schema_version"] == "2.0.0"
    assert chapter["component_id"] == "mckinsey.insight.chapter-dual-panel"
    assert chapter["layout_mode"] == "fixed_cluster"
    assert closing["component_id"] == "mckinsey.closing.source-note"
    assert closing["layout_mode"] == "fixed_cluster"


def test_real_mckinsey_atlas_exposes_contrast_cycle_progression_and_unscored_action_dimensions() -> None:
    template = PROJECT / "sources" / "麦肯锡风格.pptx"
    review = json.loads(
        (PROJECT / "analysis" / "component-review.v1.json").read_text(encoding="utf-8")
    )
    atlas = build_component_atlas(template, review)

    cases = [
        ("experimentation scale contrast", "two_sided_contrast", 2, "mckinsey.contrast.experimentation-scale"),
        ("closed-loop adoption relationship", "cycle_pair", 2, "mckinsey.cycle.adoption-loop"),
        ("workflow redesign progression", "two_stage_progression", 2, "mckinsey.progression.workflow-redesign"),
        ("management action dimensions", "icon_card_grid", 3, "mckinsey.actions.management-dimensions"),
    ]
    for semantic_use, family, count, component_id in cases:
        resolved = resolve_component_binding(atlas, {
            "semantic_use": semantic_use,
            "family": family,
            "element_count": count,
        })
        assert resolved["component_id"] == component_id
        assert resolved["binding_schema_version"] == "2.0.0"

    progression = next(
        component
        for component in atlas["components"]
        if component["component_id"] == "mckinsey.progression.workflow-redesign"
    )
    assert [
        member["shape_name"]
        for member in progression["groups"][0]["members"]
    ] == ["任意多边形: 形状 82", "任意多边形: 形状 81"]
    contrast = resolve_component_binding(atlas, {
        "semantic_use": "experimentation scale contrast",
        "family": "two_sided_contrast",
        "element_count": 2,
    })
    assert contrast["layout_mode"] == "two_sided_contrast"

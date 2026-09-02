from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from engine.manuscript_component_planner import build_manuscript_component_composition


ROOT = Path(__file__).resolve().parents[2]


def _atlas() -> dict:
    return {
        "schema_version": "1.0.0",
        "status": "reviewed",
        "source": {"sha256": "sha256:template", "slide_count": 37},
        "components": [{
            "component_id": "cards.icons",
            "family": "icon_card_grid",
            "slide_index": 5,
            "semantic_uses": ["icon capability cards"],
            "groups": [{
                "role": "segment",
                "scope": "item",
                "members": [
                    {"shape_name": f"card-{index}"}
                    for index in range(5)
                ],
            }, {
                "role": "label",
                "scope": "item",
                "bind_field": "title",
                "members": [
                    {"shape_name": f"title-{index}"}
                    for index in range(5)
                ],
            }, {
                "role": "label",
                "scope": "item",
                "bind_field": "detail",
                "members": [
                    {"shape_name": f"detail-{index}"}
                    for index in range(5)
                ],
            }],
            "parameters": {"element_count": {"minimum": 3, "maximum": 5}},
        }, {
            "component_id": "funnel.primary",
            "family": "funnel",
            "slide_index": 26,
            "semantic_uses": ["prioritization"],
            "groups": [{
                "role": "segment",
                "members": [
                    {"shape_name": f"segment-{index}"}
                    for index in range(5)
                ],
            }, {
                "role": "label",
                "members": [
                    {"shape_name": f"label-{index}"}
                    for index in range(5)
                ],
            }],
            "parameters": {"element_count": {"minimum": 1, "maximum": 8}},
        }],
    }


def _bindings(*, finding_count: int = 3, explicit_labels: bool = True) -> dict:
    finding_items = (
        [
            {"title": f"发现 {index + 1}", "detail": f"证据 {index + 1}"}
            for index in range(finding_count)
        ]
        if explicit_labels
        else [f"发现 {index + 1}" for index in range(finding_count)]
    )
    return {
        "schema": "state_ai_native_content_bindings.v1",
        "slides": [{
            "id": "key_findings",
            "title": "关键发现",
            "items": finding_items,
        }, {
            "id": "path_forward",
            "title": "前进路径",
            "items": ["设定雄心", "重塑工作流", "规模部署", "治理固化"],
        }, {
            "id": "commentary",
            "title": "评论",
            "items": ["事实", "判断"],
        }],
    }


def _storyboard() -> dict:
    return {
        "schema": "template_fill_pptx_plan.v1",
        "status": "confirmed",
        "slides": [{
            "source_slide": 1,
            "purpose": "key_findings",
            "layout_rationale": {"layout_pattern": "three conclusion cards"},
        }, {
            "source_slide": 26,
            "purpose": "path_forward",
            "layout_rationale": {"layout_pattern": "funnel priorities"},
        }, {
            "source_slide": 17,
            "purpose": "commentary",
            "layout_rationale": {"layout_pattern": "chapter insight"},
        }],
    }


def test_manuscript_planner_generates_supported_slots_and_reports_partial_coverage() -> None:
    composition = build_manuscript_component_composition(
        _atlas(), _bindings(), _storyboard(),
    )

    assert composition["schema_version"] == "1.0.0"
    assert composition["coverage"] == {
        "status": "partial",
        "total_pages": 3,
        "planned_pages": 2,
        "unsupported_pages": 1,
        "coverage_ratio": 0.6667,
    }
    assert [page["destination_slide_index"] for page in composition["pages"]] == [38, 39]
    assert composition["pages"][0]["components"][0]["placement"] == {
        "x": 0.07, "y": 0.1, "w": 0.86, "h": 0.8,
    }
    first_element = composition["pages"][0]["components"][0]["elements"][0]
    assert first_element["labels"]["title"]["text"] == "发现 1"
    assert first_element["labels"]["detail"]["text"] == "证据 1"
    assert composition["pages"][1]["components"][0]["semantic_use"] == "prioritization"
    assert composition["pages"][1]["components"][0]["elements"][0]["text"] == "设定雄心"
    assert composition["unsupported_pages"] == [{
        "output_page_index": 3,
        "purpose": "commentary",
        "layout_pattern": "chapter insight",
        "reason_code": "no_component_match",
        "reason": "no reviewed component satisfies semantic use and element capacity",
    }]


def test_manuscript_planner_reports_capacity_mismatch_without_forcing_a_component() -> None:
    composition = build_manuscript_component_composition(
        _atlas(), _bindings(finding_count=6), _storyboard(),
    )

    assert [page["purpose"] for page in composition["pages"]] == ["path_forward"]
    rejected = composition["unsupported_pages"][0]
    assert rejected["purpose"] == "key_findings"
    assert rejected["reason_code"] == "no_component_match"
    assert "capacity" in rejected["reason"]


def test_manuscript_planner_rejects_missing_explicit_extended_labels() -> None:
    composition = build_manuscript_component_composition(
        _atlas(), _bindings(explicit_labels=False), _storyboard(),
    )

    rejected = next(
        page for page in composition["unsupported_pages"]
        if page["purpose"] == "key_findings"
    )
    assert rejected["reason_code"] == "component_binding_unavailable"
    assert "requires explicit label field 'title'" in rejected["reason"]


def test_manuscript_planner_carries_item_evidence_metadata_into_labels() -> None:
    bindings = _bindings()
    bindings["slides"][0]["items"][0].update({
        "evidence_id": "src:para_1",
        "source_ref": {"source_id": "src", "loc": "para_1"},
    })

    composition = build_manuscript_component_composition(
        _atlas(), bindings, _storyboard(),
    )

    labels = composition["pages"][0]["components"][0]["elements"][0]["labels"]
    assert labels["title"]["evidence_id"] == "src:para_1"
    assert labels["detail"]["source_ref"] == {
        "source_id": "src", "loc": "para_1",
    }


def test_manuscript_planner_cli_writes_composition_and_coverage(tmp_path: Path) -> None:
    atlas_path = tmp_path / "atlas.json"
    bindings_path = tmp_path / "bindings.json"
    storyboard_path = tmp_path / "storyboard.json"
    output_path = tmp_path / "composition.json"
    atlas_path.write_text(json.dumps(_atlas()), encoding="utf-8")
    bindings_path.write_text(json.dumps(_bindings()), encoding="utf-8")
    storyboard_path.write_text(json.dumps(_storyboard()), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable, "-m", "engine", "plan-manuscript-components",
            "--component-atlas", str(atlas_path),
            "--content-bindings", str(bindings_path),
            "--storyboard", str(storyboard_path),
            "--json-out", str(output_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["coverage"]["planned_pages"] == 2
    assert len(result["unsupported_pages"]) == 1


def test_manuscript_planner_routes_cover_chapter_and_closing_without_placeholders() -> None:
    atlas = _atlas()
    atlas["components"].extend([{
        **atlas["components"][0],
        "component_id": "cover.keyword-triad",
        "semantic_uses": ["cover keywords"],
    }, {
        "component_id": "chapter.dual-panel",
        "family": "dual_panel",
        "slide_index": 31,
        "renderer": "fixed_cluster",
        "semantic_uses": ["chapter insight"],
        "groups": [{
            "role": "segment",
            "scope": "item",
            "item_indices": [0, 1],
            "members": [{"shape_name": "panel-1"}, {"shape_name": "panel-2"}],
        }, {
            "role": "label",
            "scope": "item",
            "bind_field": "title",
            "item_indices": [0, 1],
            "members": [{"shape_name": "copy-1"}, {"shape_name": "copy-2"}],
        }],
        "parameters": {"element_count": {"minimum": 2, "maximum": 2}},
    }, {
        "component_id": "closing.source-note",
        "family": "statement_card",
        "slide_index": 31,
        "renderer": "fixed_cluster",
        "semantic_uses": ["closing source note"],
        "groups": [{
            "role": "segment",
            "scope": "item",
            "item_indices": [0],
            "members": [{"shape_name": "statement-body"}],
        }, {
            "role": "label",
            "scope": "item",
            "bind_field": "title",
            "item_indices": [0],
            "members": [{"shape_name": "statement-copy"}],
        }],
        "parameters": {"element_count": {"minimum": 1, "maximum": 1}},
    }])
    bindings = {"slides": [{
        "id": "cover",
        "title": "2025 年 AI 现状",
        "items": [
            {"title": "Agents", "detail": "自主执行复杂任务"},
            {"title": "创新", "detail": "创新价值最先显现"},
            {"title": "转型", "detail": "规模化依赖工作流重构"},
        ],
    }, {
        "id": "commentary",
        "title": "从试验走向规模",
        "items": ["技术普及不等于企业价值", "规模化取决于工作流重构"],
    }, {
        "id": "closing",
        "title": "企业级价值仍待兑现",
        "subtitle": "来源：McKinsey《The state of AI in 2025》",
    }]}
    storyboard = {"slides": [{
        "purpose": "cover",
        "layout_rationale": {"layout_pattern": "three-keyword cover"},
    }, {
        "purpose": "commentary",
        "layout_rationale": {"layout_pattern": "chapter insight"},
    }, {
        "purpose": "closing",
        "layout_rationale": {"layout_pattern": "closing statement"},
    }]}

    composition = build_manuscript_component_composition(atlas, bindings, storyboard)

    assert composition["coverage"] == {
        "status": "complete",
        "total_pages": 3,
        "planned_pages": 3,
        "unsupported_pages": 0,
        "coverage_ratio": 1.0,
    }
    assert composition["unsupported_pages"] == []
    cover, chapter, closing = composition["pages"]
    assert cover["components"][0]["semantic_use"] == "cover keywords"
    assert [
        item["labels"]["title"]["text"]
        for item in cover["components"][0]["elements"]
    ] == ["Agents", "创新", "转型"]
    assert chapter["components"][0]["semantic_use"] == "chapter insight"
    assert [
        item["labels"]["title"]["text"]
        for item in chapter["components"][0]["elements"]
    ] == ["技术普及不等于企业价值", "规模化取决于工作流重构"]
    assert closing["components"][0]["semantic_use"] == "closing source note"
    assert closing["components"][0]["elements"][0]["labels"]["title"]["text"] == (
        "来源：McKinsey《The state of AI in 2025》"
    )


def test_manuscript_planner_routes_remaining_relationship_pages_without_invented_scores() -> None:
    def component(component_id: str, family: str, semantic_use: str, count: int, fields: list[str]) -> dict:
        return {
            "component_id": component_id,
            "family": family,
            "slide_index": 1,
            "renderer": "fixed_cluster",
            "semantic_uses": [semantic_use],
            "groups": [{
                "role": "segment",
                "scope": "item",
                "item_indices": list(range(count)),
                "members": [{"shape_name": f"segment-{index}"} for index in range(count)],
            }] + [{
                "role": "label",
                "scope": "item",
                "bind_field": field,
                "item_indices": list(range(count)),
                "members": [{"shape_name": f"{field}-{index}"} for index in range(count)],
            } for field in fields],
            "parameters": {"element_count": {"minimum": count, "maximum": count}},
        }

    atlas = _atlas()
    atlas["components"].extend([
        component("contrast.two-sided", "two_sided_contrast", "experimentation scale contrast", 2, ["title", "detail"]),
        component("cycle.closed-loop", "cycle_pair", "closed-loop adoption relationship", 2, ["title"]),
        component("progression.two-stage", "two_stage_progression", "workflow redesign progression", 2, ["title", "detail"]),
        {
            **atlas["components"][0],
            "component_id": "management.action-dimensions",
            "semantic_uses": ["management action dimensions"],
            "parameters": {"element_count": {"minimum": 3, "maximum": 3}},
        },
    ])
    bindings = {"slides": [{
        "id": "agents",
        "title": "Agents",
        "items": [{
            "title": "规模化",
            "detail": "23% 已规模化",
        }, {
            "title": "试验阶段",
            "detail": "39% 正在试验；多数仅覆盖一至两个职能",
        }],
    }, {
        "id": "adoption",
        "title": "采用闭环",
        "items": ["使用率从 78% 升至 88%", "覆盖扩大但嵌入不足"],
    }, {
        "id": "workflow",
        "title": "工作流",
        "items": [{
            "title": "单点用例",
            "detail": "从局部效率工具开始",
        }, {
            "title": "端到端重构",
            "detail": "高绩效者正在重塑工作流",
        }],
    }, {
        "id": "actions",
        "title": "行动框架",
        "items": [{
            "title": "界定价值目标", "detail": "明确业务结果与衡量指标",
        }, {
            "title": "选择高价值工作流", "detail": "优先重构端到端流程",
        }, {
            "title": "规模化部署并治理", "detail": "同步建立风险控制",
        }],
    }]}
    storyboard = {"slides": [{
        "purpose": "agents",
        "layout_rationale": {"layout_pattern": "two-sided contrast"},
    }, {
        "purpose": "adoption",
        "layout_rationale": {"layout_pattern": "cycle relationship"},
    }, {
        "purpose": "workflow",
        "layout_rationale": {"layout_pattern": "progression"},
    }, {
        "purpose": "actions",
        "layout_rationale": {"layout_pattern": "capability radar"},
    }]}

    composition = build_manuscript_component_composition(atlas, bindings, storyboard)

    assert composition["coverage"]["status"] == "complete"
    assert composition["unsupported_pages"] == []
    contrast, cycle, progression, actions = [page["components"][0] for page in composition["pages"]]
    assert contrast["semantic_use"] == "experimentation scale contrast"
    assert len(contrast["elements"]) == 2
    assert contrast["elements"][0]["labels"]["title"]["text"] == "规模化"
    assert contrast["elements"][1]["labels"]["title"]["text"] == "试验阶段"
    assert "多数仅覆盖一至两个职能" in contrast["elements"][1]["labels"]["detail"]["text"]
    assert cycle["semantic_use"] == "closed-loop adoption relationship"
    assert progression["semantic_use"] == "workflow redesign progression"
    assert actions["semantic_use"] == "management action dimensions"
    assert all(element["value"] is None for element in actions["elements"])


def test_manuscript_component_planner_routes_a_structured_native_chart_dashboard() -> None:
    atlas = {
        "schema_version": "1.0.0",
        "status": "reviewed",
        "source": {"sha256": "sha256:template", "slide_count": 37},
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
        "binding_name": f"bind:chart:innovation_impact:{chart_id}",
        "data": {
            "categories": ["Reported", "Other"],
            "series": [{"name": "Share", "values": values}],
        },
    } for chart_id, values in (("innovation", [64, 36]), ("ebit", [39, 61]))]
    bindings = {"slides": [{
        "id": "innovation_impact",
        "title": "AI 影响：创新领先，企业级利润仍有限",
        "dashboard": {
            "charts": charts,
            "text_bindings": [],
            "clear_text_names": ["dashboard-title"],
        },
    }]}
    storyboard = {"slides": [{
        "purpose": "innovation_impact",
        "layout_rationale": {"layout_pattern": "native chart dashboard"},
    }]}

    composition = build_manuscript_component_composition(atlas, bindings, storyboard)

    assert composition["coverage"]["status"] == "complete"
    component = composition["pages"][0]["components"][0]
    assert component["family"] == "chart_dashboard"
    assert component["element_count"] == 2
    assert component["charts"] == charts
    assert component["clear_text_names"] == ["dashboard-title"]

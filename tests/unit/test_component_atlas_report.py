from engine.component_atlas_report import (
    build_component_suitability_table,
    render_component_suitability_markdown,
)


def test_component_atlas_report_exposes_scenarios_data_and_capacity() -> None:
    atlas = {
        "status": "reviewed",
        "components": [{
            "component_id": "template.chart",
            "family": "kpi_chart_card",
            "slide_index": 4,
            "semantic_uses": ["metric comparison"],
            "topologies": ["comparison"],
            "archetypes": ["data"],
            "composition_roles": ["primary"],
            "data_contract": {"kinds": ["chart"], "chart_types": ["bar"], "max_series": 2},
            "parameters": {"element_count": {"minimum": 1, "maximum": 2}},
            "semantic_contract": {"required_fields": ["chart", "title"]},
            "text_capacity": {"title": 80},
            "native_fidelity": "exact",
            "page_guidance": {
                "can_stand_alone": False,
                "supported_page_roles": ["body"],
                "minimum_information_units": 3,
                "recommended_page_recipes": ["chart-with-insights"],
                "required_companion_roles": ["interpretation"],
                "recommended_companion_families": ["insight_card"],
                "annotation_requirements": ["value labels", "comparison baseline"],
                "prohibited_scenarios": ["chart alone on a page"],
            },
        }],
    }

    report = build_component_suitability_table(atlas)
    markdown = render_component_suitability_markdown(report)

    assert report["rows"][0]["data_kinds"] == ["chart"]
    assert report["rows"][0]["element_capacity"] == {"minimum": 1, "maximum": 2}
    assert report["rows"][0]["can_stand_alone"] is False
    assert report["rows"][0]["required_companion_roles"] == ["interpretation"]
    assert "metric comparison" in markdown
    assert "bar" in markdown
    assert "chart-with-insights" in markdown
    assert "chart alone on a page" in markdown

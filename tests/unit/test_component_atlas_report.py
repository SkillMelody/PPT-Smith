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
        }],
    }

    report = build_component_suitability_table(atlas)
    markdown = render_component_suitability_markdown(report)

    assert report["rows"][0]["data_kinds"] == ["chart"]
    assert report["rows"][0]["element_capacity"] == {"minimum": 1, "maximum": 2}
    assert "metric comparison" in markdown
    assert "bar" in markdown

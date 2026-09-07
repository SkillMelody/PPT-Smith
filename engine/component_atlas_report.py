"""Human-readable Component Atlas suitability reports."""

from __future__ import annotations


def build_component_suitability_table(atlas: dict) -> dict:
    if not isinstance(atlas, dict) or atlas.get("status") != "reviewed":
        raise ValueError("component suitability report requires a reviewed atlas")
    rows = []
    for component in atlas.get("components", []):
        count = component.get("parameters", {}).get("element_count", {})
        data = component.get("data_contract", {})
        rows.append({
            "component_id": component.get("component_id"),
            "family": component.get("family"),
            "source_slide": component.get("slide_index"),
            "suitable_scenarios": component.get("semantic_uses", []),
            "topologies": component.get("topologies", []),
            "archetypes": component.get("archetypes", []),
            "composition_roles": component.get("composition_roles", []),
            "data_kinds": data.get("kinds", ["none"]),
            "chart_types": data.get("chart_types", []),
            "data_capacity": {
                key: data.get(key) for key in (
                    "max_series", "max_categories", "max_rows", "max_columns",
                ) if data.get(key) is not None
            },
            "element_capacity": {"minimum": count.get("minimum"), "maximum": count.get("maximum")},
            "required_slots": component.get("semantic_contract", {}).get("required_fields", []),
            "text_capacity": component.get("text_capacity", {}),
            "native_fidelity": component.get("native_fidelity"),
            "renderer": component.get("renderer", "native_component"),
        })
    return {"schema_version": "1.0.0", "component_count": len(rows), "rows": rows}


def render_component_suitability_markdown(report: dict) -> str:
    lines = [
        "# Template Component Suitability Table", "",
        "| Component | Family | Suitable scenarios | Topology | Data | Elements | Required slots | Source |",
        "|---|---|---|---|---|---:|---|---:|",
    ]
    for row in report.get("rows", []):
        capacity = row.get("element_capacity", {})
        element_range = f"{capacity.get('minimum')}–{capacity.get('maximum')}"
        data = ", ".join(row.get("data_kinds", []))
        charts = row.get("chart_types", [])
        if charts:
            data += " (" + ", ".join(charts) + ")"
        values = [
            row.get("component_id", ""), row.get("family", ""),
            "; ".join(row.get("suitable_scenarios", [])),
            ", ".join(row.get("topologies", [])), data, element_range,
            ", ".join(row.get("required_slots", [])), str(row.get("source_slide", "")),
        ]
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in values) + " |")
    return "\n".join(lines) + "\n"

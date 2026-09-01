"""Build strict native-component operations from page-level semantic slots."""
from __future__ import annotations

from copy import deepcopy

from .component_atlas import select_component


def _placement(value: object, *, page_index: int, component_index: int) -> dict:
    if not isinstance(value, dict):
        raise ValueError(
            f"page {page_index} component {component_index} requires a placement object"
        )
    resolved: dict[str, float] = {}
    for key in ("x", "y", "w", "h"):
        item = value.get(key)
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"component placement {key} must be a number")
        resolved[key] = float(item)
    if resolved["x"] < 0 or resolved["y"] < 0 or resolved["w"] <= 0 or resolved["h"] <= 0:
        raise ValueError("component placement must have non-negative origin and positive size")
    if resolved["x"] + resolved["w"] > 1 or resolved["y"] + resolved["h"] > 1:
        raise ValueError("component placement must remain inside the slide")
    return resolved


def _overlaps(first: dict, second: dict) -> bool:
    return (
        max(first["x"], second["x"]) < min(first["x"] + first["w"], second["x"] + second["w"])
        and max(first["y"], second["y"]) < min(first["y"] + first["h"], second["y"] + second["h"])
    )


def _within(parent: dict, child: dict) -> dict:
    return {
        "x": round(parent["x"] + child["x"] * parent["w"], 10),
        "y": round(parent["y"] + child["y"] * parent["h"], 10),
        "w": round(child["w"] * parent["w"], 10),
        "h": round(child["h"] * parent["h"], 10),
    }


def build_component_plan(atlas: dict, composition: dict) -> dict:
    """Translate semantic page slots into fail-closed ``component_clone`` ops.

    Element capacity is derived from the actual data list.  The caller does
    not specify or hard-code a template shape count, and components occupying
    the same destination page must have non-overlapping normalized slots.
    """
    if not isinstance(composition, dict) or composition.get("schema_version") != "1.0.0":
        raise ValueError("component composition schema_version must be 1.0.0")
    pages = composition.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("component composition requires a non-empty pages list")

    operations: list[dict] = []
    selections: list[dict] = []
    for page_index, page in enumerate(pages):
        if not isinstance(page, dict):
            raise ValueError(f"page {page_index} must be an object")
        destination_slide_index = page.get("destination_slide_index")
        if (
            isinstance(destination_slide_index, bool)
            or not isinstance(destination_slide_index, int)
            or destination_slide_index < 1
        ):
            raise ValueError(f"page {page_index} requires a positive destination_slide_index")
        components = page.get("components")
        if not isinstance(components, list) or not components:
            raise ValueError(f"page {page_index} requires a non-empty components list")

        occupied: list[dict] = []
        for component_index, component in enumerate(components):
            if not isinstance(component, dict):
                raise ValueError(f"page {page_index} component {component_index} must be an object")
            placement = _placement(
                component.get("placement"),
                page_index=page_index,
                component_index=component_index,
            )
            if any(_overlaps(placement, existing) for existing in occupied):
                raise ValueError(
                    f"component slots overlap on destination slide {destination_slide_index}"
                )
            occupied.append(placement)

            component_instance_id = f"slide-{destination_slide_index}-component-{component_index + 1}"

            def expand(spec: dict, box: dict, instance_id: str, *, exact_component_id: str | None = None) -> None:
                elements = spec.get("elements")
                if isinstance(elements, list) and elements:
                    element_count = len(elements)
                else:
                    element_count = spec.get("element_count", 1 if spec.get("chart") else None)
                if isinstance(element_count, bool) or not isinstance(element_count, int) or element_count < 1:
                    raise ValueError(f"component {instance_id} requires elements or a positive element_count")
                requirement = {
                    "semantic_use": spec.get("semantic_use"),
                    "element_count": element_count,
                }
                if spec.get("family") is not None:
                    requirement["family"] = spec["family"]
                requested_component_id = exact_component_id or spec.get("component_id")
                if requested_component_id is not None:
                    requirement["component_id"] = requested_component_id
                selection = select_component(atlas, requirement)
                if selection["status"] != "selected":
                    raise ValueError(selection["reason"])
                selected = next(
                    item for item in atlas.get("components", [])
                    if item.get("component_id") == selection["component_id"]
                )
                selections.append({
                    "destination_slide_index": destination_slide_index,
                    "component_index": component_index,
                    "component_instance_id": instance_id,
                    "component_id": selection["component_id"],
                    "family": selection["family"],
                    "granularity": selected.get("granularity", "micro"),
                    "reason": selection["reason"],
                })

                children = selected.get("children", [])
                if children:
                    child_payloads = spec.get("children")
                    if not isinstance(child_payloads, dict):
                        raise ValueError(f"component {instance_id} requires child slot data")
                    known_slots = {child["slot_id"] for child in children}
                    unknown = set(child_payloads) - known_slots
                    if unknown:
                        raise ValueError(f"component {instance_id} has unknown child slots {sorted(unknown)!r}")
                    for child in children:
                        slot_id = child["slot_id"]
                        child_spec = child_payloads.get(slot_id)
                        if child_spec is None:
                            if child.get("required", True):
                                raise ValueError(f"component {instance_id} is missing required child slot {slot_id!r}")
                            continue
                        if not isinstance(child_spec, dict):
                            raise ValueError(f"component {instance_id} child slot {slot_id!r} must be an object")
                        child_component = next(
                            item for item in atlas.get("components", [])
                            if item.get("component_id") == child["component_id"]
                        )
                        resolved_child_spec = deepcopy(child_spec)
                        resolved_child_spec.setdefault(
                            "semantic_use", child_component.get("semantic_uses", [None])[0]
                        )
                        resolved_child_spec.setdefault("family", child_component.get("family"))
                        expand(
                            resolved_child_spec,
                            _within(box, child["placement"]),
                            f"{instance_id}-{slot_id}",
                            exact_component_id=child["component_id"],
                        )
                    return

                if selected.get("renderer") == "native_group":
                    text_bindings = spec.get("text_bindings")
                    if not isinstance(text_bindings, list) or not text_bindings:
                        raise ValueError(
                            f"native group component {instance_id} requires text_bindings"
                        )
                    operations.append({
                        "kind": "native_group_component_clone",
                        "destination_slide_index": destination_slide_index,
                        "component_instance_id": instance_id,
                        "component_requirement": requirement,
                        "text_bindings": deepcopy(text_bindings),
                        "placement": box,
                    })
                    return

                if any(group.get("role") == "chart" for group in selected.get("groups", [])):
                    if selected.get("family") == "chart_dashboard":
                        charts = spec.get("charts")
                        text_bindings = spec.get("text_bindings", [])
                        clear_text_names = spec.get("clear_text_names", [])
                        if not isinstance(charts, list) or len(charts) != element_count:
                            raise ValueError(
                                f"dashboard component {instance_id} requires one chart payload per element"
                            )
                        if not isinstance(text_bindings, list) or not isinstance(clear_text_names, list):
                            raise ValueError(
                                f"dashboard component {instance_id} requires text and clear lists"
                            )
                        operations.append({
                            "kind": "chart_dashboard_clone",
                            "destination_slide_index": destination_slide_index,
                            "component_instance_id": instance_id,
                            "component_requirement": requirement,
                            "charts": deepcopy(charts),
                            "text_bindings": deepcopy(text_bindings),
                            "clear_text_names": deepcopy(clear_text_names),
                            "placement": box,
                        })
                        return
                    chart = spec.get("chart")
                    text_bindings = spec.get("text_bindings", [])
                    if not isinstance(chart, dict) or not isinstance(text_bindings, list):
                        raise ValueError(f"chart component {instance_id} requires chart and text_bindings")
                    operations.append({
                        "kind": "chart_component_clone",
                        "destination_slide_index": destination_slide_index,
                        "component_instance_id": instance_id,
                        "component_requirement": requirement,
                        "chart": deepcopy(chart),
                        "text_bindings": deepcopy(text_bindings),
                        "placement": box,
                    })
                    return
                if not isinstance(elements, list) or not elements:
                    raise ValueError(f"component {instance_id} requires elements")
                operations.append({
                    "kind": "component_clone",
                    "destination_slide_index": destination_slide_index,
                    "component_instance_id": instance_id,
                    "component_requirement": requirement,
                    "elements": deepcopy(elements),
                    "placement": box,
                })

            expand(component, placement, component_instance_id)

    return {
        "schema_version": "1.0.0",
        "operations": operations,
        "selections": selections,
    }

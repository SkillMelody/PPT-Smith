"""Template-route page composition and deck-rhythm contracts.

Reviewed template components are modules, not automatically complete slides.
This module is intentionally imported only by the Template model composer and
strict Template runtime; Bespoke and Standard keep their own authoring rules.
"""

from __future__ import annotations

from collections import Counter
from math import ceil


SEMANTIC_LAYERS = frozenset({
    "assertion", "primary_evidence", "interpretation", "implication",
})
MODULE_ROLES = frozenset({
    "primary_evidence", "supporting_evidence", "interpretation", "implication",
    "context", "kpi", "annotation", "navigation", "decoration",
})
NON_SUBSTANTIVE_MODULE_ROLES = frozenset({"navigation", "decoration"})
BOUNDARY_STRATEGIES = frozenset({"reuse_template_page_recipe", "style_derived_original"})


def template_boundary_capabilities(atlas: dict) -> dict:
    """Detect reviewed full-page cover/closing recipes, not similarly named widgets."""
    roles = {"cover": [], "closing": []}
    for component in atlas.get("components", []):
        if not isinstance(component, dict):
            continue
        guidance = component.get("page_guidance", {})
        if not isinstance(guidance, dict) or guidance.get("can_stand_alone") is not True:
            continue
        if component.get("granularity") != "page_recipe":
            continue
        for role in guidance.get("supported_page_roles", []):
            if role in roles:
                roles[role].append(component.get("component_id"))
    return {
        "cover_page_recipe_component_ids": sorted(filter(None, roles["cover"])),
        "closing_page_recipe_component_ids": sorted(filter(None, roles["closing"])),
        "has_cover_page_recipe": bool(roles["cover"]),
        "has_closing_page_recipe": bool(roles["closing"]),
    }


def _issue(issues: list[dict], code: str, slide_id: str, **details) -> None:
    issues.append({"code": code, "slide_id": slide_id, **details})


def _validate_page(
    page: dict,
    slide: dict,
    *,
    capabilities: dict,
) -> tuple[dict, list[dict]]:
    slide_id = str(slide.get("id") or page.get("slide_id") or "unknown")
    issues: list[dict] = []
    contract = page.get("page_composition")
    if not isinstance(contract, dict):
        return {"slide_id": slide_id, "status": "missing"}, [{
            "code": "TEMPLATE_PAGE_COMPOSITION_MISSING", "slide_id": slide_id,
        }]

    slide_role = slide.get("slide_role", "content")
    page_role = contract.get("page_role", "body")
    expected_role = "body" if slide_role == "content" else slide_role
    if page_role != expected_role:
        _issue(
            issues, "TEMPLATE_PAGE_ROLE_MISMATCH", slide_id,
            expected_page_role=expected_role, declared_page_role=page_role,
        )

    recipe = contract.get("recipe")
    variant = contract.get("variant")
    if not isinstance(recipe, str) or not recipe:
        _issue(issues, "TEMPLATE_PAGE_RECIPE_REQUIRED", slide_id)
    if not isinstance(variant, str) or not variant:
        _issue(issues, "TEMPLATE_PAGE_VARIANT_REQUIRED", slide_id)

    layers = contract.get("semantic_layers", [])
    if not isinstance(layers, list) or any(layer not in SEMANTIC_LAYERS for layer in layers):
        _issue(issues, "TEMPLATE_PAGE_SEMANTIC_LAYERS_INVALID", slide_id)
        layers = []
    layer_set = set(layers)

    modules = contract.get("content_modules", [])
    planned_components = {
        component.get("component_id")
        for component in page.get("components", [])
        if isinstance(component, dict) and isinstance(component.get("component_id"), str)
    }
    substantive_modules: list[dict] = []
    information_units = 0
    if not isinstance(modules, list):
        _issue(issues, "TEMPLATE_PAGE_CONTENT_MODULES_INVALID", slide_id)
        modules = []
    for module_index, module in enumerate(modules, 1):
        if not isinstance(module, dict):
            _issue(
                issues, "TEMPLATE_PAGE_CONTENT_MODULE_INVALID", slide_id,
                module_index=module_index,
            )
            continue
        role = module.get("role")
        count = module.get("information_unit_count")
        component_ids = module.get("component_ids", [])
        if role not in MODULE_ROLES:
            _issue(
                issues, "TEMPLATE_PAGE_MODULE_ROLE_INVALID", slide_id,
                module_index=module_index, role=role,
            )
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            _issue(
                issues, "TEMPLATE_PAGE_INFORMATION_UNITS_INVALID", slide_id,
                module_index=module_index,
            )
            count = 0
        if (
            not isinstance(component_ids, list)
            or not component_ids
            or any(not isinstance(item, str) or not item for item in component_ids)
        ):
            _issue(
                issues, "TEMPLATE_PAGE_MODULE_COMPONENTS_INVALID", slide_id,
                module_index=module_index,
            )
            component_ids = []
        unknown = sorted(set(component_ids) - planned_components)
        if unknown:
            _issue(
                issues, "TEMPLATE_PAGE_MODULE_COMPONENT_UNKNOWN", slide_id,
                module_index=module_index, unknown_component_ids=unknown,
            )
        if role not in NON_SUBSTANTIVE_MODULE_ROLES:
            substantive_modules.append(module)
            information_units += count

    if page_role == "body":
        required_layers = {"assertion", "primary_evidence"}
        if len(layer_set) < 3 or not required_layers <= layer_set or not (
            {"interpretation", "implication"} & layer_set
        ):
            _issue(
                issues, "TEMPLATE_PAGE_SEMANTIC_LAYERS_INCOMPLETE", slide_id,
                declared_layers=sorted(layer_set),
            )
        substantive_roles = {module.get("role") for module in substantive_modules}
        if len(substantive_modules) < 2:
            _issue(
                issues, "TEMPLATE_PAGE_SINGLE_COMPONENT_SHELL", slide_id,
                substantive_module_count=len(substantive_modules),
            )
        if "primary_evidence" not in substantive_roles:
            _issue(issues, "TEMPLATE_PAGE_PRIMARY_EVIDENCE_REQUIRED", slide_id)
        if not ({"interpretation", "implication", "context", "kpi", "annotation"} & substantive_roles):
            _issue(issues, "TEMPLATE_PAGE_SUPPORTING_MODULE_REQUIRED", slide_id)
        if information_units < 4:
            _issue(
                issues, "TEMPLATE_PAGE_INFORMATION_SATURATION_LOW", slide_id,
                information_unit_count=information_units, minimum_information_units=4,
            )
        takeaway = contract.get("takeaway")
        if not isinstance(takeaway, str) or len(takeaway.strip()) < 20:
            _issue(issues, "TEMPLATE_PAGE_TAKEAWAY_REQUIRED", slide_id)

        data_shape = slide.get("component_intent", {}).get("data_shape", {})
        is_quantitative = bool(slide.get("chart") or slide.get("charts")) or (
            isinstance(data_shape, dict) and data_shape.get("kind") in {"chart", "table"}
        )
        key_numbers = contract.get("key_numbers", [])
        annotations = contract.get("chart_annotations", [])
        if is_quantitative:
            if not isinstance(key_numbers, list) or len(key_numbers) < 2:
                _issue(
                    issues, "TEMPLATE_QUANTITATIVE_PAGE_KEY_NUMBERS_REQUIRED", slide_id,
                    key_number_count=len(key_numbers) if isinstance(key_numbers, list) else 0,
                )
            if not isinstance(annotations, list) or not annotations:
                _issue(issues, "TEMPLATE_QUANTITATIVE_PAGE_ANNOTATION_REQUIRED", slide_id)

    if page_role in {"cover", "closing"}:
        strategy = contract.get("boundary_strategy")
        if strategy not in BOUNDARY_STRATEGIES:
            _issue(issues, "TEMPLATE_BOUNDARY_STRATEGY_REQUIRED", slide_id)
        capability_key = f"has_{page_role}_page_recipe"
        if capabilities.get(capability_key) is False and strategy != "style_derived_original":
            _issue(
                issues, "TEMPLATE_BOUNDARY_ORIGINAL_DESIGN_REQUIRED", slide_id,
                page_role=page_role,
            )

    return {
        "slide_id": slide_id,
        "status": "pass" if not issues else "fail",
        "page_role": page_role,
        "recipe": recipe,
        "variant": variant,
        "semantic_layers": sorted(layer_set),
        "substantive_module_count": len(substantive_modules),
        "information_unit_count": information_units,
    }, issues


def _evaluate_rhythm(page_reports: list[dict]) -> dict:
    body = [page for page in page_reports if page.get("page_role") == "body"]
    issues: list[dict] = []
    patterns = [f"{page.get('recipe')}:{page.get('variant')}" for page in body]
    recipes = [page.get("recipe") for page in body]

    run_pattern = None
    run_start = 0
    for index, pattern in enumerate(patterns, 1):
        if pattern != run_pattern:
            run_pattern, run_start = pattern, index
        if index - run_start + 1 == 3:
            issues.append({
                "code": "TEMPLATE_PAGE_PATTERN_CONSECUTIVE_LIMIT",
                "pattern": pattern,
                "first_body_page_index": run_start,
                "last_body_page_index": index,
            })

    recipe_counts = Counter(recipes)
    pattern_counts = Counter(patterns)
    body_count = len(body)
    if body_count >= 8:
        for recipe, count in sorted(recipe_counts.items()):
            ratio = count / body_count
            if ratio > 0.25:
                issues.append({
                    "code": "TEMPLATE_PAGE_RECIPE_OVERUSED",
                    "recipe": recipe, "count": count,
                    "ratio": round(ratio, 4), "maximum_ratio": 0.25,
                })
        for pattern, count in sorted(pattern_counts.items()):
            ratio = count / body_count
            if ratio > 0.20:
                issues.append({
                    "code": "TEMPLATE_PAGE_PATTERN_OVERUSED",
                    "pattern": pattern, "count": count,
                    "ratio": round(ratio, 4), "maximum_ratio": 0.20,
                })
        minimum_recipes = min(10, max(3, ceil(body_count / 5)))
        if len(recipe_counts) < minimum_recipes:
            issues.append({
                "code": "TEMPLATE_PAGE_RECIPE_DIVERSITY_LOW",
                "unique_recipe_count": len(recipe_counts),
                "minimum_unique_recipe_count": minimum_recipes,
            })

    return {
        "status": "pass" if not issues else "fail",
        "body_page_count": body_count,
        "unique_recipe_count": len(recipe_counts),
        "unique_pattern_count": len(pattern_counts),
        "recipe_counts": dict(sorted(recipe_counts.items())),
        "pattern_counts": dict(sorted(pattern_counts.items())),
        "issues": issues,
    }


def evaluate_template_page_compositions(ir: dict, atlas: dict, model_plan: dict) -> dict:
    """Validate whole-page design after component selection, before PPTX execution."""
    ir_by_id = {
        slide.get("id"): slide
        for slide in ir.get("slides", [])
        if isinstance(slide, dict) and isinstance(slide.get("id"), str)
    }
    capabilities = template_boundary_capabilities(atlas)
    reports: list[dict] = []
    issues: list[dict] = []
    for page in model_plan.get("slides", []):
        if not isinstance(page, dict):
            continue
        slide = ir_by_id.get(page.get("slide_id"), {})
        report, page_issues = _validate_page(page, slide, capabilities=capabilities)
        reports.append(report)
        issues.extend(page_issues)
    rhythm = _evaluate_rhythm(reports)
    issues.extend(rhythm["issues"])
    return {
        "status": "pass" if not issues else "fail",
        "template_boundary_capabilities": capabilities,
        "pages": reports,
        "rhythm": rhythm,
        "issues": issues,
    }

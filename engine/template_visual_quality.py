"""Archetype-aware visual density checks for Template-route candidates."""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation


GENERIC_FAMILIES = frozenset({"card_grid", "icon_card_grid"})


def _minimum_visible_text(page: dict) -> tuple[int, str]:
    archetype = page.get("archetype", "body")
    if archetype in {"cover", "section", "closing"}:
        return 30, archetype
    if page.get("chart_count", 0) >= 2:
        return 30, "data"
    families = {
        family for family in page.get("families", [])
        if isinstance(family, str)
    }
    if (
        page.get("semantic_element_count", 0) >= 2
        and families
        and not families <= GENERIC_FAMILIES
    ):
        return 50, "relationship"
    return 80, "body"


def evaluate_template_visual_quality(pages: list[dict]) -> dict:
    """Reject visually empty pages without treating charts as prose."""
    issues: list[dict] = []
    page_reports: list[dict] = []
    for index, page in enumerate(pages, 1):
        slide_id = str(page.get("slide_id") or f"S{index:02d}")
        text_chars = page.get("visible_text_chars")
        blank_score = page.get("blank_score")
        if isinstance(text_chars, bool) or not isinstance(text_chars, int) or text_chars < 0:
            issues.append({"code": "VISUAL_PAGE_METRICS_INVALID", "slide_id": slide_id})
            continue
        minimum, density_role = _minimum_visible_text(page)
        if text_chars < minimum:
            issues.append({
                "code": "VISUAL_CONTENT_DENSITY_BELOW_FLOOR",
                "slide_id": slide_id,
                "density_role": density_role,
                "visible_text_chars": text_chars,
                "minimum_visible_text_chars": minimum,
            })
        if isinstance(blank_score, (int, float)) and blank_score > 0.90:
            issues.append({
                "code": "VISUAL_PAGE_TOO_BLANK",
                "slide_id": slide_id,
                "blank_score": round(float(blank_score), 4),
                "maximum_blank_score": 0.90,
            })
        page_reports.append({
            "slide_id": slide_id,
            "density_role": density_role,
            "visible_text_chars": text_chars,
            "minimum_visible_text_chars": minimum,
            "chart_count": int(page.get("chart_count", 0)),
            "semantic_element_count": int(page.get("semantic_element_count", 0)),
            "blank_score": blank_score,
        })
    return {
        "status": "pass" if not issues else "fail",
        "pages": page_reports,
        "issues": issues,
    }


def inspect_template_visual_quality(
    pptx_path: str | Path,
    *,
    ir: dict,
    render_report: dict,
) -> dict:
    """Build density evidence from the actual PPTX and real-render report."""
    presentation = Presentation(str(pptx_path))
    ir_slides = [slide for slide in ir.get("slides", []) if isinstance(slide, dict)]
    rendered_by_index = {
        item.get("slide_index"): item
        for item in render_report.get("slides", [])
        if isinstance(item, dict)
    }
    pages: list[dict] = []
    for index, slide in enumerate(presentation.slides, 1):
        contract = ir_slides[index - 1] if index <= len(ir_slides) else {}
        text = " ".join(
            str(getattr(shape, "text", "") or "").strip()
            for shape in slide.shapes
            if getattr(shape, "has_text_frame", False)
        )
        intent = contract.get("component_intent", {})
        selected_ids = intent.get("selected_component_ids", [])
        families = (
            selected_ids
            if selected_ids
            else [f"model_authored:{intent.get('new_component_id')}"]
            if intent.get("mode") == "model_authored"
            else []
        )
        slide_role = contract.get("slide_role", "content")
        pages.append({
            "slide_id": contract.get("id", f"S{index:02d}"),
            "archetype": "body" if slide_role == "content" else slide_role,
            "visible_text_chars": len("".join(text.split())),
            "chart_count": sum(bool(getattr(shape, "has_chart", False)) for shape in slide.shapes),
            "semantic_element_count": int(intent.get("element_count", 1)),
            "families": families,
            "blank_score": rendered_by_index.get(index, {}).get("blank_score"),
        })
    return evaluate_template_visual_quality(pages)

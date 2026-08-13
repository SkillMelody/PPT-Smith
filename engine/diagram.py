"""Diagram renderers (Phase 2b): diagram_ir -> render_plan elements.

Each renderer appends builder-agnostic elements (shape / connector / textbox)
to the SlideLayout context. Positions and colors are resolved here; the
builder (PptxGenJS primary, python-pptx fallback) only translates elements
into its own API. Content-free guarantees hold: nodes/edges describe
structure, never coordinates.

Diagram families (v4.1): causal_chain is fully native; phase_roadmap and
layered_architecture use the same node/edge grid; anything unimplemented
falls back to a horizontal node strip so a diagram never renders blank.
"""

from __future__ import annotations

from .layout import _frame, _para, _run, SlideLayout

EMU_PER_IN = 914400


def _color(ctx: SlideLayout, token: str, fallback: str) -> str:
    return ctx.style.resolve_color_ref(ctx.style.color(token, fallback))


def _node_text(node: dict, index: int) -> str:
    label = str(node.get("label") or f"节点 {index + 1}")
    role = str(node.get("role") or "")
    detail = str(node.get("detail") or "")
    parts = [p for p in (label, role, detail) if p]
    return "\n".join(parts)


def _primary_nodes(diagram_ir: dict, limit: int = 5) -> list[dict]:
    nodes = diagram_ir.get("nodes", [])
    primary = [n for n in nodes if n.get("priority") != "supporting"]
    if len(primary) < 3:
        primary = list(nodes)[:3]
    return primary[:limit]


# ---- causal_chain -----------------------------------------------------------

def _causal_chain(ctx: SlideLayout, diagram_ir: dict, frame: dict) -> None:
    style = ctx.style
    nodes = _primary_nodes(diagram_ir, limit=5)
    x, y, w, h = frame["x"], frame["y"], frame["w"], frame["h"]
    gap = int(0.32 * EMU_PER_IN)
    node_w = (w - gap * (len(nodes) - 1)) // len(nodes)
    node_h = min(int(1.15 * EMU_PER_IN), h)
    top = y + (h - node_h) // 2

    accent = style.color("accent")
    surface = style.resolve_color_ref(
        style.card_tokens.get("default", {}).get("fill", "surface_1"))
    primary_text = style.color("text_primary")
    background = style.color("background")
    border = style.color("border")

    ids: list[str] = []
    for index, node in enumerate(nodes):
        eid = ctx.eid("diagram-node")
        last = index == len(nodes) - 1
        fill = accent if last else surface
        text_color = background if last else primary_text
        ctx.elements.append({
            "element_id": eid, "type": "shape", "shape": "round_rect",
            "frame": _frame(x + index * (node_w + gap), top, node_w, node_h),
            "corner_radius_emu": int(0.08 * EMU_PER_IN),
            "fill": {"color": fill},
            "stroke": {"color": border, "width_emu": 9525},
            "paragraphs": [_para([_run(_node_text(node, index), style,
                                       style.size_cpt("body", "small"),
                                       color=text_color,
                                       weight=style.weight("semibold", 600))],
                                 align="center", line_height_pct=120)],
            "editable": True, "semantic_role": "diagram_node",
        })
        ids.append(eid)
    for index in range(len(ids) - 1):
        ctx.elements.append({
            "element_id": ctx.eid("diagram-conn"), "type": "connector",
            "from_element": ids[index], "to_element": ids[index + 1],
            "route": "straight",
            "stroke": {"color": accent, "width_emu": int(1.8 * 12700)},
            "arrowhead": "end",
        })


# ---- fallback node strip ----------------------------------------------------

def _node_strip(ctx: SlideLayout, diagram_ir: dict, frame: dict) -> None:
    """Generic fallback: render nodes as a horizontal strip of cards."""
    style = ctx.style
    nodes = diagram_ir.get("nodes", [])[:6]
    if not nodes:
        ctx.degrade("builder_downgrade", "diagram_nodes_empty")
        return
    x, y, w, h = frame["x"], frame["y"], frame["w"], frame["h"]
    gap = int(0.2 * EMU_PER_IN)
    node_w = (w - gap * (len(nodes) - 1)) // len(nodes)
    node_h = min(int(1.1 * EMU_PER_IN), h)
    top = y + (h - node_h) // 2
    surface = style.resolve_color_ref(
        style.card_tokens.get("default", {}).get("fill", "surface_1"))
    primary_text = style.color("text_primary")
    border = style.color("border")

    for index, node in enumerate(nodes):
        ctx.elements.append({
            "element_id": ctx.eid("diagram-node"), "type": "shape",
            "shape": "round_rect",
            "frame": _frame(x + index * (node_w + gap), top, node_w, node_h),
            "corner_radius_emu": int(0.08 * EMU_PER_IN),
            "fill": {"color": surface},
            "stroke": {"color": border, "width_emu": 9525},
            "paragraphs": [_para([_run(_node_text(node, index), style,
                                       style.size_cpt("body", "small"),
                                       color=primary_text,
                                       weight=style.weight("semibold", 600))],
                                 align="center", line_height_pct=120)],
            "editable": True, "semantic_role": "diagram_node",
        })


# ---- chart ------------------------------------------------------------------

# IR chart type -> render-plan chart_type. combo (column + line overlay) is
# not yet a native render-plan type; degrade to column for now.
_CHART_TYPE_MAP = {
    "column": "column", "bar": "bar", "line": "line", "pie": "pie",
    "combo": "column",
}


def layout_chart(ctx: SlideLayout, chart: dict, frame: dict) -> None:
    """Emit a native chart element. Series colors resolve from the style's
    data_series palette; the builder renders the concrete chart."""
    style = ctx.style
    rp_type = _CHART_TYPE_MAP.get(chart["type"], "column")
    if chart["type"] not in _CHART_TYPE_MAP:
        ctx.degrade("chart_fallback", f"chart_{chart['type']}_column")

    palette = style.colors.get("data_series", [])
    if not palette:
        palette = [style.color("primary"), style.color("accent"),
                   style.color("positive"), style.color("text_secondary")]
    series = []
    for idx, s in enumerate(chart["data"]["series"]):
        series.append({
            "name": s["name"],
            "values": s["values"],
            "color": palette[idx % len(palette)],
        })

    ctx.elements.append({
        "element_id": ctx.eid("chart"),
        "type": "chart",
        "frame": _frame(frame["x"], frame["y"], frame["w"], frame["h"]),
        "chart_type": rp_type,
        "categories": chart["data"]["categories"],
        "series": series,
        "legend": "bottom",
        "semantic_role": "chart",
    })


# ---- dispatcher -------------------------------------------------------------

_RENDERERS = {
    "causal_chain": _causal_chain,
    # phase_roadmap / layered_architecture / drill_down_stair land in the
    # same node/edge grid; unimplemented families fall back to the strip.
    "phase_roadmap": _node_strip,
    "layered_architecture": _node_strip,
    "drill_down_stair": _node_strip,
    "interaction_storyboard": _node_strip,
    "product_ui_overview": _node_strip,
}


def layout_diagram(ctx: SlideLayout, diagram_ir: dict, frame: dict) -> None:
    dtype = diagram_ir.get("diagram_type", "")
    renderer = _RENDERERS.get(dtype)
    if renderer is None:
        ctx.degrade("builder_downgrade", f"diagram_{dtype}_unknown")
        renderer = _node_strip
    elif dtype not in ("causal_chain",):
        ctx.degrade("diagram_fallback", f"diagram_{dtype}_strip")
    renderer(ctx, diagram_ir, frame)

"""Phase 2b tests — diagram_ir/chart -> render_plan elements (v4.1).

Covers the four native diagram families migrated from v3 (causal_chain,
phase_roadmap, layered_architecture, drill_down_stair), the node-strip
fallback for unimplemented families, and chart element emission.
"""
from __future__ import annotations

from engine.diagram import layout_chart, layout_diagram
from engine.layout import SlideLayout, _frame
from engine.style_pack import load_style_pack


def _ctx() -> SlideLayout:
    return SlideLayout("s1", load_style_pack(), [])


FRAME = _frame(0, 0, 12192000, 3000000)

NODES3 = [
    {"id": "n1", "label": "问题", "priority": "primary"},
    {"id": "n2", "label": "行动", "priority": "secondary"},
    {"id": "n3", "label": "结果", "priority": "primary"},
]
NODES4 = NODES3 + [{"id": "n4", "label": "扩展", "priority": "secondary"}]


def _types(ctx: SlideLayout) -> list[str]:
    return [e["type"] for e in ctx.elements]


def _count(ctx: SlideLayout, etype: str) -> int:
    return sum(1 for e in ctx.elements if e["type"] == etype)


class TestDiagramFamilies:
    def test_causal_chain(self):
        ctx = _ctx()
        layout_diagram(ctx, {"diagram_type": "causal_chain", "nodes": NODES3}, FRAME)
        assert _count(ctx, "shape") == 3
        assert _count(ctx, "connector") == 2

    def test_phase_roadmap(self):
        ctx = _ctx()
        layout_diagram(ctx, {"diagram_type": "phase_roadmap", "nodes": NODES4}, FRAME)
        assert _count(ctx, "shape") == 4
        assert _count(ctx, "connector") == 3

    def test_layered_architecture(self):
        ctx = _ctx()
        layout_diagram(ctx, {"diagram_type": "layered_architecture", "nodes": NODES3}, FRAME)
        # boundary box + 3 layers
        assert _count(ctx, "shape") == 4
        assert _count(ctx, "connector") == 2
        # boundary box has no fill (only stroke)
        boundary = next(e for e in ctx.elements
                        if e.get("semantic_role") == "diagram_boundary")
        assert "fill" not in boundary

    def test_drill_down_stair(self):
        ctx = _ctx()
        layout_diagram(ctx, {"diagram_type": "drill_down_stair", "nodes": NODES3}, FRAME)
        assert _count(ctx, "shape") == 3
        assert _count(ctx, "connector") == 2

    def test_connectors_are_straight_with_arrow(self):
        ctx = _ctx()
        layout_diagram(ctx, {"diagram_type": "causal_chain", "nodes": NODES3}, FRAME)
        conn = next(e for e in ctx.elements if e["type"] == "connector")
        assert conn["route"] == "straight"
        assert conn["arrowhead"] == "end"


class TestFallbackAndChart:
    def test_unknown_type_falls_back_to_strip(self):
        ctx = _ctx()
        layout_diagram(ctx, {"diagram_type": "interaction_storyboard", "nodes": NODES3}, FRAME)
        # strip still renders nodes, never blank
        assert _count(ctx, "shape") >= 3
        assert any(d["kind"] == "diagram_fallback" for d in ctx.degs)

    def test_unknown_family_degrades(self):
        ctx = _ctx()
        layout_diagram(ctx, {"diagram_type": "nonsense", "nodes": NODES3}, FRAME)
        assert any(d["kind"] == "builder_downgrade" for d in ctx.degs)
        assert _count(ctx, "shape") >= 3

    def test_empty_nodes_still_ships(self):
        ctx = _ctx()
        layout_diagram(ctx, {"diagram_type": "causal_chain", "nodes": []}, FRAME)
        # no crash; degrade recorded
        assert any(d["kind"] == "builder_downgrade" for d in ctx.degs)

    def test_chart_element_emitted(self):
        ctx = _ctx()
        layout_chart(ctx, {
            "type": "column",
            "data": {"categories": ["a", "b"], "series": [{"name": "s", "values": [1, 2]}]},
        }, FRAME)
        chart = next(e for e in ctx.elements if e["type"] == "chart")
        assert chart["chart_type"] == "column"
        assert chart["series"][0]["color"].startswith("#")

    def test_chart_combo_degrades_to_column(self):
        ctx = _ctx()
        layout_chart(ctx, {
            "type": "combo",
            "data": {"categories": ["a"], "series": [{"name": "s", "values": [1]}]},
        }, FRAME)
        chart = next(e for e in ctx.elements if e["type"] == "chart")
        assert chart["chart_type"] == "column"
        assert any(d["kind"] == "chart_fallback" for d in ctx.degs)

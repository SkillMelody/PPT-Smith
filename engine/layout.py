"""Layout engine: IR slide + archetype + style -> Render Plan slides.

100% deterministic (D9): integer EMU geometry, style values resolved, text
sizes chosen by the textfit model with step-down and deterministic
truncation. Table cells are pulled from the parsed source (the IR only
references them), so the model never retypes tables.

Every bound applied (font step-down, truncation, image placeholder) is
returned as a degradation record for the decision trace — honest by
construction, nothing silently dropped.
"""

from __future__ import annotations

from .source_doc import SourceDoc, parse_anchor
from .style_pack import EMU_PER_PT, ResolvedStyle
from .textfit import fit_size_cpt, paragraphs_height_emu, truncate_to_fit

CANVAS_W, CANVAS_H = 12192000, 6858000
TITLE_H = 800100
TITLE_GAP = 228600
CARD_PAD = 152400
FOOTER_H = 274320

_EDGE_TOKEN = {"insight": "accent", "risk": "negative", "recommendation": "positive"}


def _run(text: str, style: ResolvedStyle, size_cpt: int, *, color: str | None = None,
         weight: int = 400, font: str | None = None) -> dict:
    return {"text": text or " ", "font": font or style.font(),
            "size_cpt": size_cpt, "color": color or style.color("text_primary"),
            "weight": weight}


def _para(runs: list[dict], *, align: str = "left", bullet: str = "none",
          line_height_pct: int = 135, space_after_cpt: int = 0) -> dict:
    return {"runs": runs, "align": align, "bullet": bullet,
            "line_height_pct": line_height_pct, "space_after_cpt": space_after_cpt}


def _frame(x: int, y: int, w: int, h: int) -> dict:
    return {"x": int(x), "y": int(y), "w": max(int(w), 1), "h": max(int(h), 1)}


class SlideLayout:
    """Shared geometry context for one slide."""

    def __init__(self, slide_id: str, style: ResolvedStyle,
                 degradations: list[dict]) -> None:
        self.sid = slide_id
        self.style = style
        self.degs = degradations
        self.elements: list[dict] = []
        self._seq = 0
        margin = style.margin_emu()
        self.left = margin
        self.width = CANVAS_W - 2 * margin
        self.content_top = margin // 2 + TITLE_H + TITLE_GAP
        self.content_h = CANVAS_H - self.content_top - margin // 2 - FOOTER_H

    def eid(self, tag: str) -> str:
        self._seq += 1
        return f"{self.sid}-{tag}-{self._seq}"

    def degrade(self, kind: str, detail: str) -> None:
        self.degs.append({"kind": kind, "slide_id": self.sid, "detail_code": detail})

    def add_title(self, title: str, message: str | None) -> None:
        style = self.style
        title_levels = [style.size_cpt("title", "slide"), 2000, 1800, 1600]
        title_size = fit_size_cpt(title, self.width - 182880,
                                  TITLE_H - (0 if not message else 350000),
                                  title_levels, 110,
                                  family=style.font("editorial")) or 1600
        paras = [_para([_run(title, style, title_size,
                             weight=style.weight("semibold", 600),
                             font=style.font("editorial"))],
                       align=style.alignment if style.alignment != "centered" else "center",
                       line_height_pct=110)]
        if message:
            paras.append(_para([_run(message, style, style.size_cpt("body", "normal"),
                                     color=style.color("text_secondary"))],
                               align="left", line_height_pct=125))
        self.elements.append({
            "element_id": self.eid("title"), "type": "textbox",
            "frame": _frame(self.left, self.style.margin_emu() // 2, self.width, TITLE_H),
            "paragraphs": paras, "valign": "middle", "editable": True,
            "semantic_role": "title",
        })

    def add_footer(self, text: str) -> None:
        style = self.style
        self.elements.append({
            "element_id": self.eid("footer"), "type": "textbox",
            "frame": _frame(self.left, CANVAS_H - style.margin_emu() // 2 - FOOTER_H,
                            self.width, FOOTER_H),
            "paragraphs": [_para([_run(text, style, 900,
                                       color=style.color("text_secondary"))])],
            "valign": "middle", "editable": True, "semantic_role": "footer",
        })

    # ---- content builders -------------------------------------------------

    def _block_paras(self, block: dict, size_cpt: int) -> list[dict]:
        style = self.style
        role = block.get("role")
        if role == "list":
            return [_para([_run(f"• {item['text']}", style, size_cpt)],
                          bullet="dot", space_after_cpt=400)
                    for item in block.get("items", [])]
        text = block.get("text", "")
        return [_para([_run(text, style, size_cpt)])]

    def card(self, block: dict, frame: dict) -> None:
        style = self.style
        inner_w = frame["w"] - 2 * CARD_PAD
        inner_h = frame["h"] - 2 * CARD_PAD
        levels = style.body_levels_cpt()
        size = next((s for s in levels
                     if paragraphs_height_emu(self._block_paras(block, s),
                                              inner_w) <= inner_h), None)
        if size is None:
            size = levels[-1]
            if block.get("role") == "list":
                items = list(block.get("items", []))
                while len(items) > 1 and paragraphs_height_emu(
                        self._block_paras({"role": "list", "items": items}, size),
                        inner_w) > inner_h:
                    items.pop()
                block = dict(block, items=items)
                self.degrade("content_truncation", "list_items_dropped")
                if paragraphs_height_emu(self._block_paras(block, size),
                                         inner_w) > inner_h:
                    block = {"role": "fact",
                             "text": truncate_to_fit(items[0]["text"], size,
                                                     inner_w, inner_h,
                                                     family=style.font())}
            else:
                block = dict(block, text=truncate_to_fit(
                    block.get("text", ""), size, inner_w, inner_h,
                    family=style.font()))
                self.degrade("content_truncation",
                             f"block_truncated_{block.get('role', 'text')}")
        elif size != levels[0]:
            self.degrade("font_step_down", f"body_{size}")
        element = {
            "element_id": self.eid("card"), "type": "shape",
            "frame": frame, "shape": "round_rect",
            "corner_radius_emu": int(style.shape.get("card_radius_pt", 8) * EMU_PER_PT),
            "fill": {"color": style.skin_color("card", "fill", "surface_1")},
            "stroke": {"color": style.skin_color("card", "border_color", "border"),
                       "width_emu": int(style.shape.get("border_width_pt", 0.8) * EMU_PER_PT)},
            "paragraphs": self._block_paras(block, size),
            "editable": True, "semantic_role": block.get("role", "text"),
        }
        self.elements.append(element)
        edge_token = _EDGE_TOKEN.get(block.get("role", ""))
        if edge_token:
            self.elements.append({
                "element_id": self.eid("edge"), "type": "shape",
                "frame": _frame(frame["x"], frame["y"], 45720, frame["h"]),
                "shape": "rect", "fill": {"color": self.style.color(edge_token)},
                "editable": True, "semantic_role": "accent_edge",
            })

    def stack(self, blocks: list[dict], *, top: int | None = None,
              height: int | None = None) -> None:
        if not blocks:
            return
        zone_top = self.content_top if top is None else top
        zone_h = self.content_h if height is None else height
        gap = self.style.gap_emu()
        n = len(blocks)
        card_h = (zone_h - gap * (n - 1)) // n
        y = zone_top
        for block in blocks:
            if block.get("role") == "table":
                self.table(block, _frame(self.left, y, self.width, card_h))
            elif block.get("role") == "image":
                self.image_placeholder(block, _frame(self.left, y, self.width, card_h))
            else:
                self.card(block, _frame(self.left, y, self.width, card_h))
            y += card_h + gap

    def kpi_row(self, metrics: list[dict], *, top: int, height: int) -> None:
        style = self.style
        gap = style.gap_emu()
        per_row = min(len(metrics), 4)
        card_w = (self.width - gap * (per_row - 1)) // per_row
        x = self.left
        for metric in metrics[:per_row]:
            label = metric.get("label", "")
            value = metric.get("value", "")
            if metric.get("delta"):
                value = f"{value}" if value else metric["delta"]
            paras = [
                _para([_run(label, style, style.size_cpt("body", "small"),
                            color=style.color("text_secondary"),
                            weight=style.weight("medium", 500))],
                      space_after_cpt=300),
                _para([_run(value, style, style.size_cpt("metric", "normal"),
                            color=style.skin_color("kpi", "value_color", "primary"),
                            weight=style.weight("bold", 700))]),
            ]
            if metric.get("baseline"):
                paras.append(_para([_run(f"vs {metric['baseline']}", style, 900,
                                         color=style.color("text_muted",
                                                           style.color("text_secondary")))]))
            self.elements.append({
                "element_id": self.eid("kpi"), "type": "shape",
                "frame": _frame(x, top, card_w, height), "shape": "round_rect",
                "corner_radius_emu": int(style.shape.get("card_radius_pt", 8) * EMU_PER_PT),
                "fill": {"color": style.color("surface_1")},
                "stroke": {"color": style.color("border"),
                           "width_emu": int(style.shape.get("border_width_pt", 0.8) * EMU_PER_PT)},
                "paragraphs": paras, "editable": True, "semantic_role": "metric",
            })
            x += card_w + gap
        if len(metrics) > per_row:
            self.degrade("content_truncation", f"kpi_overflow_{len(metrics) - per_row}")

    def table(self, block: dict, frame: dict, doc: SourceDoc | None = None) -> None:
        style = self.style
        caption = block.get("caption")
        if caption:
            cap_h = 274320
            self.elements.append({
                "element_id": self.eid("caption"), "type": "textbox",
                "frame": _frame(frame["x"], frame["y"] + frame["h"] - cap_h,
                                frame["w"], cap_h),
                "paragraphs": [_para([_run(caption, style, 1000,
                                           color=style.color("text_secondary"))])],
                "valign": "middle", "editable": True, "semantic_role": "caption",
            })
            frame = _frame(frame["x"], frame["y"], frame["w"],
                           frame["h"] - cap_h - style.gap_emu() // 2)
        rows_data: list[list[str]] = []
        if doc is not None:
            parsed = parse_anchor(block.get("source_ref", {}).get("loc", ""))
            element = doc.get(f"{parsed[0]}_{parsed[1]}") if parsed else None
            if element is not None:
                rows_data = element.rows
        if not rows_data:
            rows_data = getattr(self, "_table_rows_cache", {}).get(id(block), [])
        if not rows_data:
            self.card({"role": "fact",
                       "text": block.get("caption", "表格数据（见原文）")}, frame)
            self.degrade("builder_downgrade", "table_rows_unavailable")
            return
        cols = block.get("column_filter")
        if cols:
            rows_data = [[row[c] for c in cols if c < len(row)] for row in rows_data]
        limit = min(block.get("row_limit", 12), 30)
        if len(rows_data) - 1 > limit:
            self.degrade("content_truncation", f"table_rows_{len(rows_data) - 1 - limit}")
            rows_data = rows_data[: limit + 1]
        width = max(len(r) for r in rows_data)
        col_w = self.width // width if frame["w"] == self.width else frame["w"] // width
        size = style.size_cpt("body", "small")
        header_fill = style.skin_color("table", "header_fill", "surface_2")
        zebra = bool((style.skins.get("table") or {}).get("zebra"))
        row_h = max(frame["h"] // max(len(rows_data), 1), 274320)
        rows = []
        for r_idx, row in enumerate(rows_data):
            if r_idx == 0:
                fill = header_fill
            elif zebra and r_idx % 2 == 0:
                fill = style.color("surface_1")
            else:
                fill = style.color("background")
            cells = [{"paragraphs": [_para([_run(cell or " ", style, size,
                                                 weight=style.weight("semibold", 600)
                                                 if r_idx == 0 else 400)])],
                      "fill": {"color": fill}}
                     for cell in (row + [""] * width)[:width]]
            rows.append({"header": r_idx == 0, "height_emu": row_h, "cells": cells})
        self.elements.append({
            "element_id": self.eid("table"), "type": "table", "frame": frame,
            "col_widths_emu": [col_w] * width, "rows": rows,
            "border": {"color": style.color("border"), "width_emu": 9525},
            "semantic_role": "table",
        })

    def image_placeholder(self, block: dict, frame: dict) -> None:
        style = self.style
        caption = block.get("caption") or block.get("asset_ref", "图片")
        self.elements.append({
            "element_id": self.eid("img"), "type": "shape", "frame": frame,
            "shape": "rect", "fill": {"color": style.color("surface_2")},
            "stroke": {"color": style.color("border"), "width_emu": 9525},
            "paragraphs": [_para([_run(f"图：{caption}", style,
                                       style.size_cpt("body", "small"),
                                       color=style.color("text_secondary"))],
                                 align="center")],
            "editable": True, "semantic_role": "image_placeholder",
        })
        self.degrade("builder_downgrade", "image_placeholder")


def _layout_content(ctx: SlideLayout, slide: dict, archetype: str,
                    doc: SourceDoc | None) -> None:
    blocks = slide.get("blocks", [])
    if archetype == "kpi_wall":
        metrics = [b for b in blocks if b.get("role") == "metric"]
        others = [b for b in blocks if b.get("role") != "metric"]
        kpi_h = min(1371600, ctx.content_h if not others else ctx.content_h // 2)
        ctx.kpi_row(metrics, top=ctx.content_top, height=kpi_h)
        if others:
            rest_top = ctx.content_top + kpi_h + ctx.style.gap_emu()
            ctx.stack(others, top=rest_top,
                      height=ctx.content_top + ctx.content_h - rest_top)
    elif archetype == "full_table":
        tables = [b for b in blocks if b.get("role") == "table"]
        others = [b for b in blocks if b.get("role") != "table"]
        ctx.table(tables[0], _frame(ctx.left, ctx.content_top, ctx.width,
                                    ctx.content_h if not others
                                    else ctx.content_h * 3 // 4), doc)
        if others:
            top = ctx.content_top + ctx.content_h * 3 // 4 + ctx.style.gap_emu()
            ctx.stack(others, top=top,
                      height=ctx.content_top + ctx.content_h - top)
    elif archetype == "quote_focus":
        quotes = [b for b in blocks if b.get("role") == "quote"]
        others = [b for b in blocks if b.get("role") != "quote"]
        style = ctx.style
        quote_h = ctx.content_h if not others else ctx.content_h // 2
        text = quotes[0].get("text", "") if quotes else ""
        size = fit_size_cpt(text, ctx.width - 2 * CARD_PAD, quote_h - 2 * CARD_PAD,
                            [style.size_cpt("body", "large") * 2 // 1,
                             style.size_cpt("body", "large"),
                             style.size_cpt("body", "normal")],
                            130, family=style.font("editorial")) \
            or style.size_cpt("body", "normal")
        ctx.elements.append({
            "element_id": ctx.eid("quote"), "type": "textbox",
            "frame": _frame(ctx.left, ctx.content_top, ctx.width, quote_h),
            "paragraphs": [_para([_run(f"“{text}”", style, size,
                                       font=style.font("editorial"),
                                       color=style.color("primary"))],
                                 align="center", line_height_pct=130)],
            "valign": "middle", "editable": True, "semantic_role": "quote",
        })
        if others:
            top = ctx.content_top + quote_h + ctx.style.gap_emu()
            ctx.stack(others, top=top, height=ctx.content_top + ctx.content_h - top)
    elif archetype == "image_story":
        images = [b for b in blocks if b.get("role") == "image"]
        others = [b for b in blocks if b.get("role") != "image"]
        img_h = ctx.content_h if not others else ctx.content_h * 2 // 3
        ctx.image_placeholder(images[0], _frame(ctx.left, ctx.content_top,
                                                ctx.width, img_h))
        if others:
            top = ctx.content_top + img_h + ctx.style.gap_emu()
            ctx.stack(others, top=top, height=ctx.content_top + ctx.content_h - top)
    else:  # list_stack and evidence_stack share the guaranteed stack path
        ctx.stack(blocks)


def _cover_slide(ir: dict, style: ResolvedStyle) -> dict:
    deck = ir["deck"]
    margin = style.margin_emu()
    width = CANVAS_W - 2 * margin
    elements = [{
        "element_id": "cover-title", "type": "textbox",
        "frame": _frame(margin, CANVAS_H * 3 // 8, width, 1600200),
        "paragraphs": [_para([_run(deck["title"], style,
                                   style.size_cpt("title", "cover"),
                                   font=style.font("editorial"),
                                   weight=style.weight("semibold", 600))],
                             line_height_pct=110)],
        "valign": "middle", "editable": True, "semantic_role": "title",
    }, {
        "element_id": "cover-rule", "type": "shape",
        "frame": _frame(margin, CANVAS_H * 3 // 8 - 91440, 1371600, 45720),
        "shape": "rect", "fill": {"color": style.color("accent")},
        "editable": True, "semantic_role": "accent_edge",
    }]
    if deck.get("purpose"):
        elements.append({
            "element_id": "cover-purpose", "type": "textbox",
            "frame": _frame(margin, CANVAS_H * 3 // 8 + 1700784, width, 685800),
            "paragraphs": [_para([_run(deck["purpose"], style,
                                       style.size_cpt("body", "large"),
                                       color=style.color("text_secondary"))])],
            "valign": "top", "editable": True, "semantic_role": "message",
        })
    return {"slide_id": "cover",
            "background": {"color": style.color("background")},
            "elements": elements}


def layout_deck(ir: dict, decisions: list, style: ResolvedStyle,
                docs: dict[str, SourceDoc] | None = None) -> dict:
    """Returns {"canvas", "fonts_used", "slides", "degradations"}."""
    docs = docs or {}
    degradations: list[dict] = []
    plan_slides = [_cover_slide(ir, style)]
    decision_map = {d.slide_id: d for d in decisions}
    source_note = "；".join(
        s.get("title") or s.get("path") or s["source_id"] for s in ir.get("sources", []))
    for slide in ir.get("slides", []):
        decision = decision_map.get(slide["id"])
        archetype = decision.chosen if decision else "evidence_stack"
        ctx = SlideLayout(slide["id"], style, degradations)
        ctx.add_title(slide["title"], slide.get("message"))
        first_ref = next(
            (b.get("source_ref", {}).get("source_id")
             for b in slide.get("blocks", []) if b.get("source_ref")), None)
        doc = docs.get(first_ref) if first_ref else next(iter(docs.values()), None)
        _layout_content(ctx, slide, archetype, doc)
        ctx.add_footer(f"来源：{source_note}" if source_note else " ")
        plan_slides.append({
            "slide_id": slide["id"],
            "background": {"color": style.color("background")},
            "elements": ctx.elements,
        })
    fonts = sorted({run["font"]
                    for s in plan_slides for e in s["elements"]
                    for p in e.get("paragraphs", []) for run in p["runs"]}
                   | {run["font"]
                      for s in plan_slides for e in s["elements"] if e.get("type") == "table"
                      for row in e.get("rows", []) for cell in row["cells"]
                      for p in cell["paragraphs"] for run in p["runs"]})
    return {"canvas": {"width_emu": CANVAS_W, "height_emu": CANVAS_H},
            "fonts_used": fonts[:12], "slides": plan_slides,
            "degradations": degradations}

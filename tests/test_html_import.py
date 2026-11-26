#!/usr/bin/env python3
"""HTML design surface -> native scene: policy, conversion, provenance and backend extensions.

Browser-dependent checks run only when Chrome/Chromium/Edge is available; the rest need no Office.
"""
from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.design_scene import html_import as hi
from engine.design_scene.backend import inspect_objects, render
from engine.design_scene.contract import validate
from engine.design_scene.pipeline import new_task
from engine.design_scene.preflight import font_samples
from engine.design_scene.store import DesignError

MINIMAL = '<!DOCTYPE html><html><body><div id="slide" style="width:960px;height:540px"></div></body></html>'


def run(text, **style):
    base = {"stack": ["Inter", "Noto Sans CJK SC"], "size": 12, "weight": 400, "italic": False,
            "color": "rgb(30, 34, 53)", "letterSpacing": 0, "lineHeight": 16}
    return {"text": text, **base, **style}


LAYOUT = {
    "width": 960, "height": 540, "background": "rgb(244, 245, 249)", "warnings": [],
    "items": [
        {"kind": "box", "x": 20, "y": 20, "w": 300, "h": 200, "fill": "rgba(75, 79, 214, 0.5)",
         "borders": [None, None, None, None], "radius": [12, 12, 12, 12]},
        {"kind": "box", "x": 340, "y": 20, "w": 200, "h": 80, "fill": "rgb(247, 248, 252)",
         "borders": [None, None, None, {"w": 3, "c": "rgb(242, 128, 79)"}], "radius": [0, 8, 8, 0]},
        {"kind": "text", "x": 30, "y": 30, "w": 120, "h": 20, "lines": 1, "align": "left", "lineHeight": 20,
         "content": {"x": 30, "w": 280}, "cid": "p1-title", "src": None, "authored": None,
         "runs": [run("库存周转", size=16, weight=700), run(" 5.3 次", size=12)]},
        {"kind": "text", "x": 30, "y": 60, "w": 200, "h": 16, "lines": 1, "align": "left", "lineHeight": 16,
         "content": {"x": 30, "w": 280}, "cid": None, "src": "user-input.md / page-1 / block-2", "authored": "",
         "runs": [run("1 月 · 较 3 月改善")]},
        {"kind": "table", "x": 30, "y": 260, "w": 300, "h": 40, "cid": None, "src": None, "authored": None,
         "rows": [{"h": 20, "cells": [
             {"w": 100, "runs": [run("形态", size=10)], "font": run("形态"), "align": "left", "valign": "middle",
              "fill": None, "pad": [2, 6, 2, 6], "borderBottom": {"w": 1, "c": "rgb(230, 232, 240)"}},
             {"w": 200, "runs": [run("周转次数", size=10)], "font": run("周转次数"), "align": "right", "valign": "middle",
              "fill": None, "pad": [2, 6, 2, 6], "borderBottom": {"w": 1, "c": "rgb(230, 232, 240)"}}]},
                  {"h": 20, "cells": [
             {"w": 100, "runs": [run("成品", weight=700)], "font": run("成品"), "align": "left", "valign": "middle",
              "fill": "rgb(238, 240, 251)", "pad": [2, 6, 2, 6], "borderBottom": None},
             {"w": 200, "runs": [run("4.3", weight=700)], "font": run("4.3"), "align": "right", "valign": "middle",
              "fill": "rgb(238, 240, 251)", "pad": [2, 6, 2, 6], "borderBottom": None}]}]},
        {"kind": "chart", "x": 560, "y": 260, "w": 300, "h": 160, "cid": "p1-trend", "src": None, "authored": None,
         "spec": {"type": "line", "categories": ["1月", "2月", "3月"], "min": 0, "max": 20, "major": 5,
                  "series": [{"name": "呆滞占比（%）", "values": [12, 14, 11], "color": "F2804F", "area": True}]}},
        {"kind": "path", "ox": 600, "oy": 40, "sx": 1, "sy": 1, "d": "M0,0 C50,0 50,40 100,40 L100,60 C50,60 50,20 0,20 Z",
         "fill": "rgb(43, 185, 169)", "fillOpacity": 0.5, "stroke": None, "strokeWidth": 0, "strokeOpacity": 1},
    ],
}
SOURCE = "第01页｜库存\n库存周转\t5.3 次\n形态\t周转次数\n成品\t4.3\n呆滞占比\t12\t14\t11\n1月\t2月\t3月\n缺货率\t2.9\n"


def compiled_task():
    task = new_task("html-import-test", mode="create", width=960, height=540, pages=1, author="test")
    task["design"]["brief"] = "HTML import fixture"
    task["content"]["notes"].append({"page_id": "page-1", "text": "Fixture note."})
    items, nodes, background, notes, authored = hi.to_scene(LAYOUT, "page-1", task["canvas"],
                                                            default_source="user-input.md / page-1")
    untraced = hi.trace(items, SOURCE, authored)
    candidate, reset, _ = hi.apply(task, "page-1", items, nodes, background)
    return candidate, items, nodes, notes, untraced, reset


class PolicyTests(unittest.TestCase):
    def test_minimal_page_passes(self):
        self.assertEqual(hi.check_policy(MINIMAL)["status"], "passed")

    def test_active_and_external_content_rejected(self):
        bad = {
            "<script>": MINIMAL.replace("</body>", "<script>alert(1)</script></body>"),
            "<img>": MINIMAL.replace("</div>", '<img alt="x"></div>'),
            "onclick": MINIMAL.replace('id="slide"', 'id="slide" onclick="x()"'),
            "href": MINIMAL.replace("</div>", '<a href="https://example.com">x</a></div>'),
            "url(": MINIMAL.replace("height:540px", "height:540px;background:url(a.png)"),
            "@import": MINIMAL.replace("<body>", "<body><style>@import 'x.css';</style>"),
            "@font-face": MINIMAL.replace("<body>", "<body><style>@font-face{font-family:x}</style>"),
            "svg use": MINIMAL.replace("</div>", "<svg><use></use></svg></div>"),
        }
        for label, text in bad.items():
            with self.subTest(label), self.assertRaises(DesignError):
                hi.check_policy(text)

    def test_slide_root_required_once(self):
        with self.assertRaisesRegex(DesignError, "HTML_SLIDE_ROOT_REQUIRED"):
            hi.check_policy("<html><body><div></div></body></html>")


class ConversionTests(unittest.TestCase):
    def test_compact_imported_page_before_authoring_notes(self):
        from engine.design_scene.authoring import compact, expand
        task, *_ = compiled_task()
        task["design"]["brief"] = ""
        task["content"]["notes"] = []
        doc = compact(task)
        self.assertEqual(expand(doc, complete=False), task)
        with self.assertRaisesRegex(DesignError, "DESIGN_BRIEF_REQUIRED"):
            expand(doc)
        doc["task"]["design"]["brief"] = "Compare inventory changes."
        doc["task"]["content"]["notes"] = [{"page_id": "page-1", "text": "Values from the supplied manuscript."}]
        self.assertEqual(validate(expand(doc), complete=True)["status"], "valid")

    def setUp(self):
        self.task, self.items, self.nodes, self.notes, self.untraced, self.reset = compiled_task()

    def test_scene_validates_complete_and_binds_every_record_once(self):
        self.assertEqual(self.untraced, [])
        self.assertEqual(validate(self.task, complete=True)["status"], "valid")

    def test_geometry_and_style_mapping(self):
        by = {n["type"]: [m for m in self.nodes if m["type"] == n["type"]] for n in self.nodes}
        rounded = by["shape"][0]
        self.assertEqual(rounded["shape"], "rounded_rect")
        self.assertAlmostEqual(rounded["style"]["fill_alpha"], 0.5)
        self.assertEqual(rounded["style"]["radius"], 12)
        # Non-uniform radius compiles into a native cubic-Bezier path, with a left accent as its own native rectangle.
        asym_path = next(p for p in by["path"] if p["box"]["x"] == 340 and p["box"]["y"] == 20)
        self.assertIn("C", [c["op"] for c in asym_path["commands"]])
        self.assertTrue(any(s["box"]["width"] == 3 and s["style"]["fill"] == "F2804F" for s in by["shape"]))
        title = by["text"][0]
        self.assertEqual(title["font"]["ea_family"], "Noto Sans CJK SC")
        self.assertFalse(title["wrap"])
        self.assertEqual(title["spans"][0]["start"], 4)
        svg_path = next(p for p in by["path"] if [c["op"] for c in p["commands"]] == ["M", "C", "L", "C", "Z"])
        self.assertEqual(svg_path["style"]["fill_alpha"], 0.5)
        table = by["table"][0]
        self.assertEqual(sum(table["column_widths"]), table["box"]["width"])
        self.assertEqual(table["cell_styles"][1][0]["fill"], "EEF0FB")
        chart = by["chart"][0]
        self.assertEqual(chart["area_series"], [0])
        self.assertEqual(chart["axis"]["max"], 20)
        self.assertEqual(chart["font"]["family"], "Inter")  # follows the page's dominant face

    def test_content_ids_and_provenance(self):
        ids = {c["id"] for c in self.items}
        self.assertIn("p1-title", ids)
        authored = next(c for c in self.items if c["text" if c["type"] == "text" else "id"] == "1 月 · 较 3 月改善")
        self.assertTrue(authored["provenance"]["checked"])
        self.assertTrue(authored["provenance"]["uncertainties"])
        self.assertEqual(authored["provenance"]["source"], "user-input.md / page-1 / block-2")

    def test_untraced_text_is_reported_not_checked(self):
        items, _, _, _, authored = hi.to_scene({**LAYOUT, "items": [{**LAYOUT["items"][2], "cid": None,
                                                                    "runs": [run("编造的结论")]}]},
                                               "page-1", {"width": 960, "height": 540}, default_source="x")
        untraced = hi.trace(items, SOURCE, authored)
        self.assertEqual(len(untraced), 1)
        self.assertFalse(items[0]["provenance"]["checked"])

    def test_coverage_reports_missing_numbers(self):
        report = hi.coverage(SOURCE, self.items)
        self.assertIn("2.9", report["missing_numbers"])
        self.assertNotIn("4.3", report["missing_numbers"])

    def test_render_and_object_inspection(self):
        data = render(self.task, {})
        inspect_objects(data, self.task)  # chart series compare must ignore the area overlay
        with ZipFile(io.BytesIO(data)) as z:
            slide = z.read("ppt/slides/slide1.xml").decode()
            chart = next(z.read(n).decode() for n in z.namelist() if n.startswith("ppt/charts/chart"))
        self.assertIn('<a:alpha val="50000"/>', slide)
        self.assertIn('typeface="Noto Sans CJK SC"', slide)
        self.assertIn("{2D5ABB26-0587-4C30-8999-92F81FD0307C}", slide)
        self.assertIn("<c:areaChart>", chart)
        self.assertIn('<c:crossBetween val="between"/>', chart)
        self.assertLess(chart.index("<c:crossBetween"), chart.index("<c:majorUnit"))

    def test_composition_reset_when_ids_disappear(self):
        task = self.task
        task["design"]["pages"][0]["composition"] = {
            "page_role": "body", "claim_content_id": "p1-title", "content_relation": "r", "layout_family": "l",
            "reading_path": ["p1-title", "p1-trend"], "information_attachment": "mixed",
            "layer_plan": {"primary": "a", "secondary": "b", "detail": "c"}, "rationale": "x"}
        layout = {**LAYOUT, "items": [i for i in LAYOUT["items"] if i.get("cid") != "p1-trend"]}
        items, nodes, bg, _, authored = hi.to_scene(layout, "page-1", task["canvas"], default_source="x")
        hi.trace(items, SOURCE, authored)
        candidate, reset, _ = hi.apply(task, "page-1", items, nodes, bg)
        self.assertTrue(reset)
        self.assertNotIn("composition", candidate["design"]["pages"][0])

    def test_font_probe_routes_east_asian_glyphs_to_ea_face(self):
        faces = {(s["family"], s["bold"]): s["text"] for s in font_samples(self.task)}
        self.assertIn("库", faces[("Noto Sans CJK SC", True)])
        self.assertNotIn("库", faces.get(("Inter", True), ""))


def text_item(text, x, y, w=120, h=16, size=12, authored=None, container=None, overflow=None):
    return {"kind": "text", "x": x, "y": y, "w": w, "h": h, "lines": 1, "align": "left", "lineHeight": 16,
            "content": {"x": x, "w": w}, "cid": None, "src": None, "authored": authored,
            "container": container, "overflow": overflow or {"x": 0, "y": 0}, "runs": [run(text, size=size)]}


class AuthoredAndSourceTests(unittest.TestCase):
    def scene(self, *items, kind="user"):
        return hi.to_scene({**LAYOUT, "items": list(items)}, "page-1", {"width": 960, "height": 540},
                           default_source="report.md / p3", source_kind=kind)

    def test_authored_wording_cannot_introduce_numbers(self):
        items, _, _, _, authored = self.scene(text_item("成品周转 4.3 次，较上期提升 18%", 10, 10, authored="wording"))
        untraced = hi.trace(items, SOURCE, authored)
        self.assertEqual(untraced[0]["reason"], "authored_numbers_not_in_source")
        self.assertEqual(untraced[0]["missing"], ["18"])

    def test_nav_and_derived_are_accepted_with_notes(self):
        items, _, _, _, authored = self.scene(text_item("03 / 18", 10, 10, authored="nav"),
                                              text_item("合计 9.6", 10, 40, authored="derived"))
        self.assertEqual(hi.trace(items, SOURCE, authored), [])
        self.assertIn("navigation", items[0]["provenance"]["uncertainties"][0])
        self.assertIn("derived", items[1]["provenance"]["uncertainties"][0])

    def test_invalid_authored_kind_rejected(self):
        with self.assertRaisesRegex(DesignError, "HTML_AUTHORED_KIND_INVALID"):
            self.scene(text_item("x", 10, 10, authored="guess"))

    def test_document_source_kind(self):
        items, *_ = self.scene(text_item("库存周转", 10, 10), kind="document")
        self.assertEqual(items[0]["provenance"]["kind"], "document")
        self.assertEqual(items[0]["provenance"]["source"], "report.md / p3")

    def test_table_cell_level_derived_preserves_tracing_for_other_cells(self):
        table = {
            "kind": "table", "x": 10, "y": 10, "w": 300, "h": 60, "cid": "tbl-1", "src": None, "authored": None,
            "rows": [
                {"h": 30, "cells": [
                    {"w": 150, "runs": [run("形态")], "font": {"size": 11, "color": "rgb(0,0,0)", "stack": ["Inter"], "weight": 400, "italic": False, "lineHeight": 14}, "align": "left", "valign": "middle", "fill": None, "borderBottom": None, "pad": [2, 4, 2, 4]},
                    {"w": 150, "runs": [run("合计 9.6")], "font": {"size": 11, "color": "rgb(0,0,0)", "stack": ["Inter"], "weight": 400, "italic": False, "lineHeight": 14}, "align": "right", "valign": "middle", "fill": None, "borderBottom": None, "pad": [2, 4, 2, 4], "authored": "derived"},
                ]},
                {"h": 30, "cells": [
                    {"w": 150, "runs": [run("4.3")], "font": {"size": 11, "color": "rgb(0,0,0)", "stack": ["Inter"], "weight": 400, "italic": False, "lineHeight": 14}, "align": "right", "valign": "middle", "fill": None, "borderBottom": None, "pad": [2, 4, 2, 4]},
                    {"w": 150, "runs": [run("虚构999")], "font": {"size": 11, "color": "rgb(0,0,0)", "stack": ["Inter"], "weight": 400, "italic": False, "lineHeight": 14}, "align": "right", "valign": "middle", "fill": None, "borderBottom": None, "pad": [2, 4, 2, 4]},
                ]},
            ],
        }
        items, _, _, _, authored = self.scene(table)
        untraced = hi.trace(items, SOURCE, authored)
        self.assertEqual(len(untraced), 1)
        self.assertEqual(untraced[0]["missing"], ["虚构999"])
        self.assertFalse(items[0]["provenance"]["checked"])

        table["rows"][1]["cells"][1]["runs"] = [run("成品")]
        items_ok, _, _, _, authored_ok = self.scene(table)
        self.assertEqual(hi.trace(items_ok, SOURCE, authored_ok), [])
        self.assertTrue(items_ok[0]["provenance"]["checked"])
        self.assertTrue(any("table cells (derived)" in u for u in items_ok[0]["provenance"]["uncertainties"]))

    def test_lint_errors_block_task_mutation(self):
        from unittest import mock
        task = new_task("lint-block", mode="create", width=960, height=540, pages=1, author="test")
        bad_layout = {
            "width": 960, "height": 540, "background": "rgb(255,255,255)", "warnings": [],
            "items": [text_item("库存周转", 10, 10), text_item("库存周转", 40, 12)],
        }
        with mock.patch.object(hi, "render_layout", return_value=(bad_layout, b"\x89PNG")):
            candidate, report, *_ = hi.import_html(task, "page-1", MINIMAL, default_source="x", assume_checked=True)
        self.assertIsNone(candidate)
        self.assertEqual(report["status"], "imported_with_lint_errors")
        self.assertGreater(report["design_lint"]["errors"], 0)


class LintTests(unittest.TestCase):
    def codes(self, *items):
        return {f["code"] for f in hi.lint({"items": list(items)}, {"width": 960, "height": 540})["findings"]}

    def test_overlap_outside_and_container(self):
        card = {"x": 0, "y": 0, "w": 100, "h": 30}
        codes = self.codes(text_item("标签甲", 10, 10), text_item("标签乙", 60, 14),
                           text_item("出界", 900, 530), text_item("溢出卡片", 10, 20, container=card),
                           text_item("固定框溢出", 300, 300, overflow={"x": 0, "y": 16}))
        self.assertTrue({"TEXT_OVERLAP", "OUTSIDE_SLIDE", "TEXT_OUTSIDE_CONTAINER", "TEXT_OVERFLOWS_BOX"} <= codes)

    def test_cjk_text_needs_cjk_face_in_stack(self):
        latin_only = text_item("经营概况", 10, 10)
        latin_only["runs"][0]["stack"] = ["Inter"]
        self.assertIn("CJK_TEXT_WITHOUT_CJK_FONT", self.codes(latin_only))
        self.assertNotIn("CJK_TEXT_WITHOUT_CJK_FONT", self.codes(text_item("经营概况", 10, 10)))

    def test_glyph_ink_is_not_overflow(self):
        self.assertNotIn("TEXT_OVERFLOWS_BOX", self.codes(text_item("标题", 10, 10, overflow={"x": 0, "y": 4})))

    def test_hierarchy_and_small_text(self):
        self.assertIn("FLAT_HIERARCHY", self.codes(text_item("a", 10, 10), text_item("b", 10, 40)))
        weak = self.codes(text_item("标题", 10, 10, size=16), text_item("正文正文正文", 10, 40, size=12),
                          text_item("注", 10, 70, size=10))
        self.assertIn("WEAK_HIERARCHY", weak)
        self.assertIn("SMALL_TEXT", self.codes(text_item("小字", 10, 10, size=5)))
        clean = self.codes(text_item("主数字", 10, 10, size=40), text_item("正文正文正文正文", 10, 80, size=12),
                           text_item("注释", 10, 120, size=10))
        self.assertFalse(clean & {"FLAT_HIERARCHY", "WEAK_HIERARCHY", "SMALL_TEXT"})


class BleedTests(unittest.TestCase):
    def test_bleeding_circle_becomes_clipped_path(self):
        layout = {**LAYOUT, "items": [{"kind": "box", "x": 800, "y": -100, "w": 300, "h": 300,
                                       "fill": "rgba(75, 79, 214, 0.35)", "borders": [None] * 4, "radius": [150] * 4},
                                      LAYOUT["items"][2]]}
        task = new_task("bleed", mode="create", width=960, height=540, pages=1, author="test")
        task["design"]["brief"] = "bleed fixture"
        task["content"]["notes"].append({"page_id": "page-1", "text": "n"})
        items, nodes, bg, notes, authored = hi.to_scene(layout, "page-1", task["canvas"], default_source="x")
        self.assertEqual(hi.trace(items, SOURCE, authored), [])
        self.assertEqual(nodes[0]["type"], "path")
        b = nodes[0]["box"]
        self.assertAlmostEqual(b["x"] + b["width"], 960, delta=0.1)
        self.assertAlmostEqual(b["y"], 0, delta=0.1)
        self.assertAlmostEqual(nodes[0]["style"]["fill_alpha"], 0.35)
        self.assertTrue(any(n["code"] == "BLEED_SHAPE_CLIPPED_TO_SLIDE" for n in notes))
        candidate, *_ = hi.apply(task, "page-1", items, nodes, bg)
        self.assertEqual(validate(candidate)["status"], "valid")
        render(candidate, {})


class ImageTests(unittest.TestCase):
    def task_with(self, role):
        task = new_task("img", mode="create", width=960, height=540, pages=1, author="test")
        task["assets"]["items"].append({"id": "logo", "sha256": "a" * 64, "original_sha256": "b" * 64, "width": 10,
                                        "height": 10, "page_ids": [], "role": role, "source": "user upload"})
        return task

    def image_scene(self, task):
        layout = {**LAYOUT, "items": [{"kind": "image", "x": 20, "y": 20, "w": 120, "h": 40, "asset": "logo",
                                       "fit": "contain", "radius": 6, "cid": None, "src": None, "authored": None}]}
        return hi.to_scene(layout, "page-1", task["canvas"], default_source="x")

    def test_image_node_and_page_attachment(self):
        task = self.task_with("photo")
        items, nodes, bg, notes, _ = self.image_scene(task)
        self.assertEqual(nodes[0]["type"], "image")
        self.assertEqual(nodes[0]["asset_id"], "logo")
        self.assertEqual(nodes[0]["radius"], 6)
        candidate, _, attached = hi.apply(task, "page-1", items, nodes, bg)
        self.assertEqual(attached, ["logo"])
        self.assertIn("page-1", candidate["assets"]["items"][0]["page_ids"])
        # Verify rounded image renders with transparent corners and opaque center.
        import io as _io
        from PIL import Image as _Image
        from zipfile import ZipFile as _ZipFile
        raw_buf = _io.BytesIO()
        _Image.new("RGB", (120, 40), (30, 90, 200)).save(raw_buf, format="PNG")
        candidate["design"]["brief"] = "Rounded photo test."
        candidate["content"]["notes"] = [{"page_id": "page-1", "text": "Photo note."}]
        candidate["content"]["items"].append({
            "id": "p1-cap", "page_id": "page-1", "type": "text", "text": "Logo",
            "required_edit": "native",
            "provenance": {"kind": "user", "source": "x", "checked": True, "uncertainties": []},
        })
        candidate["scene"]["pages"][0]["nodes"].append({
            "id": "p1-cap-node", "page_id": "page-1", "type": "text", "role": "native_text",
            "content_id": "p1-cap", "box": {"x": 20, "y": 80, "width": 120, "height": 20}, "z": 1,
            "font": {"family": "Inter", "size": 12, "color": "111111"},
            "align": "left", "valign": "top", "wrap": True,
        })
        pptx_bytes = render(candidate, {"logo": raw_buf.getvalue()})
        with _ZipFile(_io.BytesIO(pptx_bytes)) as zf:
            media = [n for n in zf.namelist() if n.startswith("ppt/media/")]
            self.assertEqual(len(media), 1)
            out_img = _Image.open(_io.BytesIO(zf.read(media[0]))).convert("RGBA")
            self.assertEqual(out_img.getpixel((0, 0))[3], 0)
            self.assertEqual(out_img.getpixel((out_img.width // 2, out_img.height // 2))[3], 255)

    def test_reference_and_unknown_assets_rejected(self):
        task = self.task_with("reference")
        items, nodes, bg, *_ = self.image_scene(task)
        with self.assertRaisesRegex(DesignError, "HTML_ASSET_ROLE_NOT_PLACEABLE"):
            hi.apply(task, "page-1", items, nodes, bg)
        task["assets"]["items"].clear()
        with self.assertRaisesRegex(DesignError, "HTML_ASSET_UNKNOWN"):
            hi.apply(task, "page-1", items, nodes, bg)
        with self.assertRaisesRegex(DesignError, "HTML_ASSET_UNKNOWN"):
            hi._asset_css('<div data-asset="ghost"></div>', {})
        # Commented-out data-asset must be ignored, while invalid IDs are rejected.
        self.assertEqual(hi._asset_css('<!-- <div data-asset="ghost"></div> --><div id="slide"></div>', {}), "")
        with self.assertRaisesRegex(DesignError, "HTML_ASSET_ID_INVALID"):
            hi._asset_css('<div id="slide"><div data-asset="bad\\"css"></div></div>', {})


class SourceTests(unittest.TestCase):
    def test_segment_by_page_heading(self):
        text = "前言\n第01页｜A\na1\n第02页｜B\nb1\n第03页｜C\n"
        self.assertEqual(hi.source_segment(text, "第02页"), "第02页｜B\nb1")
        with self.assertRaises(DesignError):
            hi.source_segment(text, "第09页")


class LegacyCompatibilityTests(unittest.TestCase):
    def test_new_fields_are_optional(self):
        task = new_task("legacy", mode="create", width=960, height=540, pages=1, author="test")
        task["content"]["items"].append({"id": "t", "page_id": "page-1", "type": "text", "text": "x",
                                         "required_edit": "native",
                                         "provenance": {"kind": "user", "source": "s", "checked": True, "uncertainties": []}})
        task["scene"]["pages"][0]["nodes"].append({
            "id": "n", "page_id": "page-1", "type": "text", "role": "native_text", "content_id": "t",
            "box": {"x": 0, "y": 0, "width": 100, "height": 20}, "z": 0,
            "font": {"family": "Arial", "size": 12, "color": "000000"}, "align": "left", "valign": "top", "wrap": True})
        self.assertEqual(validate(task)["status"], "valid")


class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = hi.browser_capabilities()
        if not result["available"]:
            code = result["reason"]
            if code in {"HTML_BROWSER_NOT_FOUND", "HTML_BROWSER_PERMISSION_DENIED", "HTML_BROWSER_LAUNCH_FAILED",
                        "HTML_BROWSER_SANDBOX_BLOCKED", "HTML_BROWSER_TIMEOUT"}:
                raise unittest.SkipTest(f"{code}: {result['detail']}")
            raise AssertionError(result)

    def test_real_layout_extraction(self):
        page = ('<!DOCTYPE html><html><head><style>*{margin:0}#slide{position:relative;width:960px;height:540px;'
                'background:#fff;font-family:"Noto Sans CJK SC",sans-serif}.c{position:absolute;left:40px;top:40px;'
                'width:300px;padding:10px;border-radius:8px;background:rgba(75,79,214,.2)}'
                '.t{font:700 20px/28px "Noto Sans CJK SC"}</style></head><body><div id="slide"><div class="c">'
                '<div class="t" data-cid="hello">库存周转 <span style="font-weight:400">5.3 次</span></div></div>'
                '<table><tr><td>形态</td><td>4.3</td></tr></table></div></body></html>')
        hi.check_policy(page)
        layout, png = hi.render_layout(page, 960, 540)
        self.assertTrue(png.startswith(b"\x89PNG"))
        kinds = [i["kind"] for i in layout["items"]]
        self.assertIn("box", kinds)
        self.assertIn("table", kinds)
        text = next(i for i in layout["items"] if i["kind"] == "text")
        self.assertEqual(text["cid"], "hello")
        self.assertEqual(len(text["runs"]), 2)
        self.assertAlmostEqual(text["y"], 50, delta=6)

    def test_inline_content_and_merged_table_round_trip(self):
        page = """<!DOCTYPE html><html><head><style>
          #slide { width:960px; height:540px; font:16px Arial; background:white }
          table { border-collapse:collapse; width:300px } td { border:2px solid #234567 }
          </style></head><body><div id="slide">
          <div data-cid="kpi"><span>92</span><span hidden>draft</span><b>%</b><br><span>done</span></div>
          <table data-cid="records"><tbody>
          <tr><td rowspan="0" colspan="2">A<b style="color:#ab1234">B</b></td><td>C</td></tr>
          <tr><td><p>D<span style="visibility:hidden">raft</span></p><div><b>total</b></div></td></tr></tbody>
          <tbody><tr><td>L</td><td>M</td><td>N</td></tr></tbody>
          </table></div></body></html>"""
        task = new_task("rich-html", mode="create", width=960, height=540, pages=1, author="test")
        task["design"]["brief"] = "inline and table"
        task["content"]["notes"].append({"page_id": "page-1", "text": "n"})
        candidate, report, *_ = hi.import_html(task, "page-1", page, default_source="fixture", assume_checked=True)
        self.assertEqual(report["objects"]["text"], 1)
        items = {item["id"]: item for item in candidate["content"]["items"]}
        self.assertEqual(items["kpi"]["text"], "92%\ndone")
        self.assertEqual(items["records"]["cells"], [["AB", "", "C"], ["", "", "D\ntotal"], ["L", "M", "N"]])
        styles = next(n["cell_styles"] for n in candidate["scene"]["pages"][0]["nodes"] if n["type"] == "table")
        origin = styles[0][0]
        self.assertEqual((origin["row_span"], origin["col_span"]), (2, 2))
        self.assertEqual(origin["spans"][0]["font"]["color"], "AB1234")
        self.assertTrue(styles[1][2]["spans"][-1]["font"]["bold"])
        for side in ("left", "right", "top", "bottom"):
            self.assertEqual(origin["border_" + side]["color"], "234567")
        inspect_objects(render(candidate, {}), candidate)

    def test_bundled_example_imports_cleanly(self):
        text = (Path(__file__).resolve().parents[1] / "examples/html-design/indicator-columns.html").read_text("utf-8")
        task = new_task("example", mode="create", width=960, height=540, pages=1, author="test")
        task["design"]["brief"] = "example"
        task["content"]["notes"].append({"page_id": "page-1", "text": "n"})
        candidate, report, layout, png = hi.import_html(task, "page-1", text, default_source="example",
                                                        assume_checked=True)
        self.assertEqual(report["status"], "imported", report.get("browser_warnings"))
        self.assertEqual(report["objects"]["chart"], 1)
        self.assertEqual(report["objects"]["table"], 1)
        self.assertEqual(report["objects"]["path"], 1)
        self.assertEqual(validate(candidate, complete=True)["status"], "valid")
        inspect_objects(render(candidate, {}), candidate)

    def test_asset_preview_is_injected_by_the_tool(self):
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (40, 20), (220, 30, 30)).save(buf, "PNG")
        task = new_task("img", mode="create", width=960, height=540, pages=1, author="test")
        task["assets"]["items"].append({"id": "logo", "sha256": "a" * 64, "original_sha256": "b" * 64, "width": 40,
                                        "height": 20, "page_ids": ["page-1"], "role": "photo", "source": "user upload"})
        page = ('<!DOCTYPE html><html><body style="margin:0"><div id="slide" style="position:relative;width:960px;'
                'height:540px;background:#fff"><div data-asset="logo" data-fit="cover" style="position:absolute;'
                'left:100px;top:100px;width:200px;height:100px"></div></div></body></html>')
        candidate, report, layout, png = hi.import_html(task, "page-1", page, default_source="x", assume_checked=True,
                                                        asset_bytes={"logo": buf.getvalue()})
        self.assertEqual(report["objects"]["image"], 1)
        shot = Image.open(io.BytesIO(png)).convert("RGB")
        scale = shot.width / 960
        self.assertEqual(shot.getpixel((int(200 * scale), int(150 * scale))), (220, 30, 30))
        node = candidate["scene"]["pages"][0]["nodes"][0]
        self.assertEqual((node["type"], node["fit"]), ("image", "cover"))

    def test_size_mismatch_rejected(self):
        with self.assertRaisesRegex(DesignError, "HTML_SLIDE_SIZE_MISMATCH"):
            hi.render_layout(MINIMAL.replace("960px", "1000px"), 960, 540)

    def test_svg_primitives_compile_with_viewbox_and_relative_commands(self):
        markup = ('<svg data-native-svg="" width="200" height="100" viewBox="10 20 100 50">'
                  '<g transform="translate(2 1)"><line x1="10" y1="20" x2="20" y2="25" stroke="black"/>'
                  '<rect x="22" y="24" width="10" height="5" rx="1"/><circle cx="45" cy="35" r="5"/>'
                  '<polygon points="55,30 60,40 65,30"/><path d="m70 30 h10 v10 h-10z"/></g></svg>')
        page = '<div id="slide" style="width:960px;height:540px">' + markup + '<p>Geometry</p></div>'
        hi.check_policy(page)
        layout, _ = hi.render_layout(page, 960, 540)
        self.assertEqual(layout["warnings"], [])
        task = new_task("svg-fixture", mode="create", width=960, height=540, pages=1, author="test")
        task["design"]["brief"] = "Explain the five native shapes."
        task["content"]["notes"].append({"page_id": "page-1", "text": "The source uses one shared viewBox."})
        items, nodes, bg, _, _ = hi.to_scene(layout, "page-1", task["canvas"], default_source="svg")
        self.assertEqual([n["type"] for n in nodes], ["path"] * 5 + ["text"])
        self.assertEqual(hi.trace(items, "Geometry"), [])
        self.assertEqual(nodes[0]["box"], {"x": 4, "y": 2, "width": 20, "height": 10})
        self.assertEqual(sum(c["op"] == "C" for c in nodes[2]["commands"]), 4)
        candidate, *_ = hi.apply(task, "page-1", items, nodes, bg)
        inspect_objects(render(candidate, {}), candidate)

    def test_percentage_radius_and_inline_block_pill_without_false_overlap(self):
        page = """<!DOCTYPE html><html><head><style>
          *{margin:0;box-sizing:border-box}
          #slide{position:relative;width:960px;height:540px;background:#fff;font:16px Arial}
          .circle{position:absolute;left:40px;top:40px;width:200px;height:200px;background:#4B4FD6;border-radius:50%}
          .row{position:absolute;left:280px;top:60px;width:400px;font:16px/24px Arial}
          .pill{display:inline-block;margin-left:8px;padding:2px 8px;background:#EEF0FB;border-radius:6px}
        </style></head><body><div id="slide">
          <div class="circle"></div>
          <div class="row">Status:<span class="pill">Ready</span></div>
        </div></body></html>"""
        task = new_task("pill-circle", mode="create", width=960, height=540, pages=1, author="test")
        candidate, report, layout, _ = hi.import_html(task, "page-1", page, default_source="x", assume_checked=True)
        self.assertIsNotNone(candidate)
        self.assertEqual(report["design_lint"]["errors"], 0, report["design_lint"])
        circle = next(n for n in candidate["scene"]["pages"][0]["nodes"] if n["type"] == "shape" and n["style"].get("fill") == "4B4FD6")
        self.assertAlmostEqual(circle["style"]["radius"], 100.0, delta=0.5)


if __name__ == "__main__":
    unittest.main()

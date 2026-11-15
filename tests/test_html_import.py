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
         "content": {"x": 30, "w": 280}, "cid": "p1-title", "src": None, "authored": False,
         "runs": [run("库存周转", size=16, weight=700), run(" 5.3 次", size=12)]},
        {"kind": "text", "x": 30, "y": 60, "w": 200, "h": 16, "lines": 1, "align": "left", "lineHeight": 16,
         "content": {"x": 30, "w": 280}, "cid": None, "src": "user-input.md / page-1 / block-2", "authored": True,
         "runs": [run("6 月 · 较 1 月改善")]},
        {"kind": "table", "x": 30, "y": 260, "w": 300, "h": 40, "cid": None, "src": None, "authored": False,
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
        {"kind": "chart", "x": 560, "y": 260, "w": 300, "h": 160, "cid": "p1-trend", "src": None, "authored": False,
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
    items, nodes, background, notes = hi.to_scene(LAYOUT, "page-1", task["canvas"], default_source="user-input.md / page-1")
    untraced = hi.trace(items, SOURCE)
    candidate, reset = hi.apply(task, "page-1", items, nodes, background)
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
        # Non-uniform radius -> squared, with a left accent drawn as its own native rectangle.
        self.assertTrue(any(n["code"] == "NONUNIFORM_RADIUS_SQUARED" for n in self.notes))
        self.assertTrue(any(s["box"]["width"] == 3 and s["style"]["fill"] == "F2804F" for s in by["shape"]))
        title = by["text"][0]
        self.assertEqual(title["font"]["ea_family"], "Noto Sans CJK SC")
        self.assertFalse(title["wrap"])
        self.assertEqual(title["spans"][0]["start"], 4)
        self.assertEqual(by["path"][0]["style"]["fill_alpha"], 0.5)
        self.assertEqual([c["op"] for c in by["path"][0]["commands"]], ["M", "C", "L", "C", "Z"])
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
        authored = next(c for c in self.items if c["text" if c["type"] == "text" else "id"] == "6 月 · 较 1 月改善")
        self.assertTrue(authored["provenance"]["checked"])
        self.assertTrue(authored["provenance"]["uncertainties"])
        self.assertEqual(authored["provenance"]["source"], "user-input.md / page-1 / block-2")

    def test_untraced_text_is_reported_not_checked(self):
        items, *_ = hi.to_scene({**LAYOUT, "items": [{**LAYOUT["items"][2], "cid": None,
                                                      "runs": [run("编造的结论")]}]},
                                "page-1", {"width": 960, "height": 540}, default_source="x")
        untraced = hi.trace(items, SOURCE)
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
        items, nodes, bg, _ = hi.to_scene(layout, "page-1", task["canvas"], default_source="x")
        hi.trace(items, SOURCE)
        candidate, reset = hi.apply(task, "page-1", items, nodes, bg)
        self.assertTrue(reset)
        self.assertNotIn("composition", candidate["design"]["pages"][0])

    def test_font_probe_routes_east_asian_glyphs_to_ea_face(self):
        faces = {(s["family"], s["bold"]): s["text"] for s in font_samples(self.task)}
        self.assertIn("库", faces[("Noto Sans CJK SC", True)])
        self.assertNotIn("库", faces.get(("Inter", True), ""))


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


@unittest.skipUnless(hi.find_browser(), "Chrome/Chromium/Edge not installed")
class BrowserTests(unittest.TestCase):
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

    def test_size_mismatch_rejected(self):
        with self.assertRaisesRegex(DesignError, "HTML_SLIDE_SIZE_MISMATCH"):
            hi.render_layout(MINIMAL.replace("960px", "1000px"), 960, 540)


if __name__ == "__main__":
    unittest.main()

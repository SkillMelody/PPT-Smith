"""Public HTML chart options, input errors and native-template route regressions."""
import html
import io
import json
import unittest
from contextlib import redirect_stdout
from zipfile import ZipFile

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.enum.chart import XL_LEGEND_POSITION

from engine.__main__ import main as engine_main
from engine.design_scene import html_import as hi
from engine.design_scene.backend import inspect_objects, render
from engine.design_scene.cli import route
from engine.design_scene.pipeline import new_task
from engine.design_scene.store import DesignError


def chart_page(spec):
    attr = html.escape(json.dumps(spec), quote=True)
    return (f'<html><body style="margin:0"><div id="slide" style="width:400px;height:240px;background:white">'
            f'<div data-chart="{attr}" style="width:400px;height:240px"></div></div></body></html>')


SERIES = [{"name": "Volumes", "values": [0.25, 0.75]}]
CATS = ["R&D", "Operations"]


class HtmlChartTests(unittest.TestCase):
    def test_native_sector_chart(self):
        for kind in ("pie", "doughnut"):
            with self.subTest(kind=kind):
                spec = {"type": kind, "categories": CATS, "series": SERIES, "label_number_format": "0%",
                        "legend": True, "legend_position": "right" if kind == "doughnut" else "bottom",
                        "colors": ["#3333ff", "#009933"],
                        "label_colors": ["ffffff"], **({"hole_size": 65} if kind == "doughnut" else {})}
                hi.check_policy(chart_page(spec))
                layout = {"width": 400, "height": 240, "background": "rgb(255,255,255)",
                          "items": [{"kind": "chart", "x": 10, "y": 10, "w": 380, "h": 220, "spec": spec}]}
                task = new_task("chart", mode="create", width=400, height=240, pages=1, author="test")
                task["design"]["brief"] = "Show the two-part distribution."
                task["content"]["notes"].append({"page_id": "page-1", "text": "R&D accounts for a quarter."})
                items, nodes, bg, _, authored = hi.to_scene(layout, "page-1", task["canvas"], default_source="source")
                self.assertEqual(nodes[0]["colors"], ["3333FF", "009933"])
                self.assertEqual(hi.trace(items, "Volumes: R&D 0.25, Operations 0.75", authored), [])
                candidate, *_ = hi.apply(task, "page-1", items, nodes, bg)
                pptx = render(candidate, {})
                inspect_objects(pptx, candidate)
                with ZipFile(io.BytesIO(pptx)) as z:
                    chart = etree.fromstring(z.read("ppt/charts/chart1.xml"))
                ns = {"c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
                      "a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
                self.assertTrue(chart.xpath(f"//c:{kind}Chart/c:ser", namespaces=ns))
                self.assertIn("0%", chart.xpath("//c:dLbls//c:numFmt/@formatCode", namespaces=ns))
                self.assertIn("FFFFFF", chart.xpath("//c:dLbl//a:srgbClr/@val", namespaces=ns))
                reopened = next(s.chart for s in Presentation(io.BytesIO(pptx)).slides[0].shapes if s.has_chart)
                self.assertEqual(reopened.legend.position, XL_LEGEND_POSITION.RIGHT if kind == "doughnut"
                                 else XL_LEGEND_POSITION.BOTTOM)
                if kind == "doughnut":
                    self.assertEqual(chart.xpath("//c:holeSize/@val", namespaces=ns), ["65"])

    def test_invalid_input_rejected_before_browser(self):
        base = {"categories": CATS, "series": SERIES}
        for changes in ({"major": 0}, {"major": 0.00001},
                        {"series": [None]}, {"series": [{"name": "x", "values": [0]}]},
                        {"type": "pie", "series": [{"name": "x", "values": [0, 0]}]},
                        {"type": "pie", "series": SERIES * 2}, {"hole_size": 65}, {"colors": ["peach"]},
                        {"legend": "false"}, {"axis": {"min": 5, "max": 3}}, {"label_num_format": "0.0"}):
            with self.subTest(changes=changes), self.assertRaisesRegex(DesignError, "HTML_CHART_DATA_INVALID"):
                hi.check_policy(chart_page({**base, **changes}))
        with self.assertRaisesRegex(DesignError, "HTML_CHART_DATA_INVALID"):
            hi.check_policy('<div id="slide"><div data-chart="invalid"></div></div>')
        with self.assertRaisesRegex(DesignError, "HTML_CHART_TYPE_UNSUPPORTED"):
            hi.check_policy(chart_page({**base, "type": "scatter"}))
        long_id = 9_007_199_254_740_993
        for spec in ({**base, "categories": [long_id, "B"]},
                     {**base, "series": [{**SERIES[0], "name": long_id}]}):
            with self.subTest(spec=spec), self.assertRaisesRegex(DesignError, "use a quoted string"):
                hi.check_policy(chart_page(spec))
        hi.check_policy(chart_page({**base, "categories": [str(long_id), "B"]}))

    def test_numeric_categories_and_series_name(self):
        spec = {"categories": [2025, 2026], "series": [{"name": 1, "values": ["0.25", 0.75]}],
                "legend": True, "legend_position": "bottom", "label_number_format": "0.0%"}
        layout = {"background": "rgb(255,255,255)", "items": [
            {"kind": "chart", "x": 0, "y": 0, "w": 300, "h": 200, "spec": spec}]}
        items, nodes, *_ = hi.to_scene(layout, "page-1", {"width": 400, "height": 240}, default_source="source")
        self.assertEqual(items[0]["categories"], ["2025", "2026"])
        self.assertEqual(items[0]["series"], [{"name": "1", "values": [0.25, 0.75]}])
        self.assertEqual(nodes[0]["label_number_format"], "0.0%")

    def test_stacked_charts_and_axis_number_format(self):
        for kind in ("stacked_column", "stacked_bar"):
            with self.subTest(kind=kind):
                spec = {
                    "type": kind, "categories": ["Q1", "Q2"],
                    "series": [{"name": "Core", "values": [0.4, 0.5], "color": "4B4FD6"},
                               {"name": "New", "values": [0.2, 0.3], "color": "2BB9A9"}],
                    "label_number_format": "0%", "axis_number_format": "0%", "legend": True,
                }
                hi.check_policy(chart_page(spec))
                layout = {"width": 400, "height": 240, "background": "rgb(255,255,255)",
                          "items": [{"kind": "chart", "x": 10, "y": 10, "w": 380, "h": 220, "spec": spec}]}
                task = new_task("stacked", mode="create", width=400, height=240, pages=1, author="test")
                task["design"]["brief"] = "Stacked breakdown."
                task["content"]["notes"].append({"page_id": "page-1", "text": "Stacked note."})
                items, nodes, bg, _, authored = hi.to_scene(layout, "page-1", task["canvas"], default_source="source")
                self.assertEqual(nodes[0]["chart_type"], kind)
                self.assertEqual(nodes[0]["label_position"], "center")
                self.assertEqual(nodes[0]["axis"]["number_format"], "0%")
                self.assertEqual(hi.trace(items, "Q1 0.4 0.2 Q2 0.5 0.3", authored), [])
                candidate, *_ = hi.apply(task, "page-1", items, nodes, bg)
                pptx = render(candidate, {})
                inspect_objects(pptx, candidate)
                with ZipFile(io.BytesIO(pptx)) as z:
                    chart = etree.fromstring(z.read("ppt/charts/chart1.xml"))
                ns = {"c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
                      "a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
                self.assertEqual(chart.xpath("//c:barChart/c:grouping/@val", namespaces=ns), ["stacked"])
                self.assertIn("0%", chart.xpath("//c:valAx/c:numFmt/@formatCode", namespaces=ns))
                # Inside-bar labels must contrast with each series fill instead of matching it.
                label_colors = chart.xpath("//c:barChart/c:ser/c:dLbls/c:txPr//a:srgbClr/@val", namespaces=ns)
                self.assertEqual(label_colors, ["FFFFFF", "1E2235"])

    def test_template_route(self):
        selection = route(template=True)
        self.assertEqual(selection["entrypoint"], "engine template")
        self.assertEqual(selection["guide"], "references/native-template-workflow.md")
        self.assertEqual(route(template=True, template_use="style")["intent"], "create")
        help_out = io.StringIO()
        with redirect_stdout(help_out), self.assertRaises(SystemExit) as exit_status:
            engine_main(["--help"])
        self.assertEqual(exit_status.exception.code, 0)
        self.assertIn("engine template capabilities", help_out.getvalue())

    def test_browser_doughnut_preview(self):
        capability = hi.browser_capabilities()
        if not capability["available"]:
            if capability["reason"] in {"HTML_BROWSER_NOT_FOUND", "HTML_BROWSER_PERMISSION_DENIED",
                                        "HTML_BROWSER_LAUNCH_FAILED", "HTML_BROWSER_SANDBOX_BLOCKED", "HTML_BROWSER_TIMEOUT"}:
                self.skipTest(capability["reason"])
            self.fail(str(capability))
        spec = {"type": "doughnut", "categories": CATS, "series": SERIES, "colors": ["BB0000", "00BB00"],
                "labels": False, "hole_size": 65}
        page = chart_page(spec)
        hi.check_policy(page)
        layout, png = hi.render_layout(page, 400, 240)
        self.assertFalse(layout["warnings"])
        shot = Image.open(io.BytesIO(png)).convert("RGB")
        scale = shot.width / 400
        pixel = lambda x, y: shot.getpixel((round(x * scale), round(y * scale)))
        self.assertEqual(pixel(200, 120), (255, 255, 255))
        self.assertEqual(pixel(260, 60), (187, 0, 0))
        self.assertEqual(pixel(140, 180), (0, 187, 0))

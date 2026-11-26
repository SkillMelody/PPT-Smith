import unittest

from engine.design_scene import html_import as hi
from engine.design_scene.store import DesignError


class TraceTests(unittest.TestCase):
    def test_chart_trace_checks_sign_grouping_and_precision(self):
        for source, value, expected in [
            ("A −3.2%", -3.2, True), ("A − 3.2%", -3.2, True), ("A − 3.2%", 3.2, False),
            ("A -3.2%", 3.2, False),
            ("A 12.0", 12, True), ("A +１，２３４.５", 1234.5, True),
            ("A 1,234.5", 234.5, False), ("A 1234567.89", 1234567.89, True),
            ("A 0.000000032", 3.2e-8, True),
        ]:
            with self.subTest(source=source, value=value):
                chart = {"type": "chart", "id": "c", "categories": ["A"], "series": [{"values": [value]}],
                         "provenance": {"checked": True}}
                errors = hi.trace([chart], source)
                self.assertEqual(not errors, expected)
                self.assertEqual(chart["provenance"]["checked"], expected)

    def test_wrong_sign_fails_wording_and_literal_records(self):
        for mode in ({}, {"c": "wording"}):
            item = {"type": "text", "id": "c", "text": "3.2%", "provenance": {}}
            self.assertTrue(hi.trace([item], "-3.2%", mode))
            self.assertFalse(item["provenance"]["checked"])

    def test_literal_number_and_surrounding_words_need_one_source_match(self):
        for source, value in [
            ("本期 -3.2%，去年 3.2 元", "3.2%"),
            ("销售312万元，人数12人", "12万元"),
            ("预算 1,234.5 元，另有 234.5 件", "234.5元"),
            ("表中数值：1\t2，另一项为12件", "表中数值：12"),
        ]:
            for entry in ({"type": "text", "text": value}, {"type": "table", "cells": [[value]]}):
                with self.subTest(source=source, entry=entry):
                    item = {**entry, "id": "c", "provenance": {"checked": True}}
                    self.assertTrue(hi.trace([item], source))
                    self.assertFalse(item["provenance"]["checked"])
                    self.assertFalse(hi.trace([item], source + "\n" + value))

    def test_wording_and_coverage_keep_explicit_percent_unit(self):
        item = {"id": "c", "type": "text", "text": "上升 +3.20％", "provenance": {}}
        self.assertTrue(hi.trace([item], "本期 -3.2%，去年 3.2 元", {"c": "wording"}))
        self.assertFalse(hi.trace([item], "原稿 +３.２ %", {"c": "wording"}))
        self.assertTrue(hi.coverage("增长 3.2%", [{"type": "text", "text": "3.20件"}])["missing_numbers"])
        self.assertFalse(hi.coverage("增长 3.2%", [item])["missing_numbers"])

    def test_chart_raw_values_cover_a_unit_supplied_in_the_source(self):
        chart = {"type": "chart", "id": "c", "categories": ["A"],
                 "series": [{"name": "变化率（%）", "values": [-3.2]}], "provenance": {}}
        source = "A −3.20%"
        self.assertFalse(hi.trace([chart], source, {"c": "wording"}))
        self.assertFalse(hi.coverage(source, [chart])["missing_numbers"])

    def test_coverage_includes_first_line_and_omits_only_requested_heading(self):
        shown = [{"type": "text", "text": "1234.5 和 +3.2%"}]
        self.assertEqual(hi.coverage("缺口 -3.2%\n合计 1,234.50", shown)["missing_numbers"], ["-3.2"])
        self.assertEqual(hi.coverage("第09页｜收入 78\n正文", shown, source_heading="第09页")["missing_numbers"], ["78"])


class PathAndFontTests(unittest.TestCase):
    def test_relative_curves_and_close_reset(self):
        self.assertEqual(hi._parse_path("m1 2 3 4 h2 v-1 q1 0 2 1 c0 1 2 3 4 5 z m1 1", 2, 1),
                         [("M", [(2, 2)]), ("L", [(8, 6)]), ("L", [(12, 6)]), ("L", [(12, 5)]),
                          ("Q", [(14, 5), (16, 6)]), ("C", [(16, 7), (20, 9), (24, 11)]),
                          ("Z", []), ("M", [(4, 3)])])
        for path in ("M 1 2 A 4 3 0 0 0 0 0", "M 2 1 @ L 4 5", "M0 0 L2", "M0 0 Z 2 3",
                     "M,0,0 L2 3", "M0,,0 L2 3", "M0 0, L2 3"):
            with self.subTest(path=path), self.assertRaises(DesignError):
                hi._parse_path(path, 1, 1)

    def test_cjk_aliases_select_an_east_asian_face(self):
        for family in ("SimSun", "DengXian", "WenQuanYi", "LXGW", "等线"):
            run = dict(stack=["Inter", family], size=12, weight=400, italic=False, color="rgb(0,0,0)")
            with self.subTest(family=family):
                self.assertEqual(hi._font(run)["ea_family"], family)

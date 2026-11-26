"""Regression tests for skill release hygiene, schema parity, preflight coverage, and background image lint."""
from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

import engine
from engine.design_scene.contract import SCHEMA
from engine.design_scene.html_import import lint
from engine.design_scene.pipeline import new_task
from engine.design_scene.preflight import GLYPHS_PER_PAGE, font_samples
from scripts import check_identity

ROOT = Path(__file__).resolve().parents[1]


class SkillHygieneTests(unittest.TestCase):
    def test_design_task_schema_matches_runtime_contract(self):
        disk = json.loads((ROOT / "schemas" / "design-task.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(disk, SCHEMA)

    def test_version_and_identity_are_synchronized(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(engine.__version__, version)
        self.assertEqual(check_identity.check(ROOT), [])

    def test_skill_md_has_no_high_entropy_findings_or_allowlist_entry(self):
        from scripts import audit_bundle
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertFalse(any(audit_bundle.HIGH_ENTROPY.search(line) for line in text.splitlines()))
        allowlist = json.loads((ROOT / "packaging" / "audit-allowlist.json").read_text(encoding="utf-8"))
        self.assertNotIn("SKILL.md", {entry["path"] for entry in allowlist.get("allowlist", [])})


class PreflightGlyphCoverageTests(unittest.TestCase):
    def test_long_cjk_deck_splits_across_probe_pages_without_dropping_symbols(self):
        task = new_task("glyph-coverage", mode="create", width=960, height=540, pages=1)
        # 320 unique CJK characters + ASCII + rare arrows/warnings that used to be truncated past 160 chars.
        cjk = "".join(chr(0x4E00 + i) for i in range(320))
        symbols = "⇄⚠→₂✓"
        text = "ABC123" + cjk + symbols
        task["content"]["items"].append({
            "id": "p1-body", "page_id": "page-1", "type": "text", "text": text,
            "required_edit": "native",
            "provenance": {"kind": "user", "source": "test", "checked": True, "uncertainties": []},
        })
        task["scene"]["pages"][0]["nodes"].append({
            "id": "n1", "page_id": "page-1", "type": "text", "role": "native_text",
            "content_id": "p1-body", "box": {"x": 20, "y": 20, "width": 800, "height": 400}, "z": 0,
            "font": {"family": "Inter", "ea_family": "Noto Sans CJK SC", "size": 14, "color": "111111"},
            "align": "left", "valign": "top", "wrap": True,
        })
        samples = font_samples(task)
        ea_samples = [s for s in samples if s["family"] == "Noto Sans CJK SC"]
        latin_samples = [s for s in samples if s["family"] == "Inter"]
        # 320 unique CJK characters exceed GLYPHS_PER_PAGE -> split across 2 pages with 0 untested glyphs.
        self.assertGreaterEqual(len(ea_samples), 2)
        self.assertEqual(sum(s["untested_glyphs"] for s in samples), 0)
        self.assertEqual(set("".join(s["text"] for s in ea_samples)), set(cjk))
        # Special symbols must appear in the first Inter chunk ahead of ASCII.
        self.assertTrue(set(symbols) <= set(latin_samples[0]["text"]))
        self.assertLess(latin_samples[0]["text"].index("⇄"), latin_samples[0]["text"].index("A"))
        self.assertTrue(all(len(s["text"]) <= GLYPHS_PER_PAGE for s in samples))

    def test_chart_number_format_symbols_enter_font_preflight(self):
        task = new_task("chart-fmt-glyphs", mode="create", width=960, height=540, pages=1)
        task["content"]["items"].append({
            "id": "c1", "page_id": "page-1", "type": "chart", "categories": ["Q1"],
            "series": [{"name": "Rev", "values": [12]}], "data_basis": "user_data",
            "required_edit": "native",
            "provenance": {"kind": "user", "source": "test", "checked": True, "uncertainties": []},
        })
        task["scene"]["pages"][0]["nodes"].append({
            "id": "n1", "page_id": "page-1", "type": "chart", "role": "native_chart",
            "content_id": "c1", "chart_type": "column", "box": {"x": 20, "y": 20, "width": 400, "height": 200},
            "z": 0, "font": {"family": "Inter", "ea_family": "Noto Sans CJK SC", "size": 10, "color": "111111"},
            "colors": ["4B4FD6"], "legend": False, "labels": True,
            "label_number_format": '"¥"0"万"', "axis": {"number_format": '0"亿"'},
        })
        samples = font_samples(task)
        ea_text = "".join(s["text"] for s in samples if s["family"] == "Noto Sans CJK SC")
        latin_text = "".join(s["text"] for s in samples if s["family"] == "Inter")
        self.assertIn("万", ea_text)
        self.assertIn("亿", ea_text)
        self.assertIn("¥", latin_text)

    def test_text_height_risk_respects_explicit_line_height(self):
        from engine.design_scene.contract import validate
        task = new_task("lh-check", mode="create", width=960, height=540, pages=1)
        task["content"]["items"].append({
            "id": "kpi", "page_id": "page-1", "type": "text", "text": "92%",
            "required_edit": "native",
            "provenance": {"kind": "user", "source": "test", "checked": True, "uncertainties": []},
        })
        node = {
            "id": "n1", "page_id": "page-1", "type": "text", "role": "native_text",
            "content_id": "kpi", "box": {"x": 20, "y": 20, "width": 120, "height": 38}, "z": 0,
            "font": {"family": "Inter", "size": 34, "color": "111111"},
            "align": "left", "valign": "top", "wrap": False, "line_height": 38,
        }
        task["scene"]["pages"][0]["nodes"].append(node)
        self.assertFalse(any(w["code"] == "TEXT_HEIGHT_RISK" for w in validate(task)["warnings"]))
        node["box"]["height"] = 30
        self.assertTrue(any(w["code"] == "TEXT_HEIGHT_RISK" for w in validate(task)["warnings"]))


class BackgroundImageLintTests(unittest.TestCase):
    def _text(self, x=60, y=120, w=400, h=60, text="封面主标题"):
        return {
            "kind": "text", "x": x, "y": y, "w": w, "h": h, "lines": 1, "lineHeight": 40,
            "align": "left", "content": {"x": x, "w": w}, "overflow": {"x": 0, "y": 0}, "container": None,
            "runs": [{"text": text, "stack": ["Noto Sans CJK SC"], "size": 32, "weight": 700,
                      "italic": False, "color": "rgb(255,255,255)", "letterSpacing": 0}],
        }

    def test_explicit_or_cover_backdrop_image_downgrades_overlap_to_warning(self):
        canvas = {"width": 960, "height": 540}
        # 1. Explicit data-image-layer="background"
        layout_explicit = {"items": [
            {"kind": "image", "x": 0, "y": 0, "w": 450, "h": 540, "asset": "hero", "fit": "cover", "layer": "background"},
            self._text(),
        ]}
        res1 = lint(layout_explicit, canvas)
        self.assertEqual(res1["errors"], 0)
        self.assertIn("TEXT_OVER_BACKGROUND_IMAGE", {f["code"] for f in res1["findings"]})

        # 2. Full-bleed cover image painted before text
        layout_cover = {"items": [
            {"kind": "image", "x": 0, "y": 0, "w": 960, "h": 540, "asset": "cover-bg", "fit": "cover"},
            self._text(),
        ]}
        res2 = lint(layout_cover, canvas)
        self.assertEqual(res2["errors"], 0)
        self.assertIn("TEXT_OVER_BACKGROUND_IMAGE", {f["code"] for f in res2["findings"]})

        # 3. Foreground illustration colliding with text still triggers blocking error
        layout_fg = {"items": [
            {"kind": "image", "x": 50, "y": 100, "w": 200, "h": 150, "asset": "diagram", "fit": "contain"},
            self._text(),
        ]}
        res3 = lint(layout_fg, canvas)
        self.assertEqual(res3["errors"], 1)
        self.assertIn("TEXT_OVERLAP", {f["code"] for f in res3["findings"]})


class LightweightMetaAndPageCommandsTests(unittest.TestCase):
    def test_set_meta_set_page_and_page_lifecycle_cli(self):
        import io
        from contextlib import redirect_stdout
        from tempfile import TemporaryDirectory
        from engine.design_scene.cli import main as design_main
        from engine.design_scene.store import DesignError
        from engine.design_scene.authoring import add_page, remove_page, reorder_pages, set_meta, set_page

        def run_cli(*argv):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = design_main(list(argv))
            return rc, json.loads(buf.getvalue())

        tmp_base = ROOT / ".pytest-tmp"
        tmp_base.mkdir(exist_ok=True)
        with TemporaryDirectory(dir=tmp_base) as tmp:
            task_dir = Path(tmp).resolve() / "task"
            rc, res = run_cli("init", "--task-dir", str(task_dir), "--task-id", "meta-test", "--pages", "2")
            self.assertEqual(rc, 0, res)

            (task_dir / "brief.md").write_text("Executive Q3 deck with dark navy header.", encoding="utf-8")
            rc, res = run_cli("set-meta", "--task-dir", str(task_dir), "--brief-file", "brief.md",
                              "--audience", "管理层", "--review-profile", "decorative_business")
            self.assertEqual(rc, 0)
            self.assertIn("design.brief", res["updated"])
            self.assertIn("design.review_profile", res["updated"])

            # Add a third page between page-1 and page-2
            rc, res = run_cli("add-page", "--task-dir", str(task_dir), "--page", "page-mid",
                              "--after", "page-1", "--background", "#F4F5F9")
            self.assertEqual(rc, 0)
            self.assertEqual(res["pages"], ["page-1", "page-mid", "page-2"])

            # Seed one content item on page-1 so composition.reading_path can bind to it
            task = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
            task["content"]["items"].append({
                "id": "p1-title", "page_id": "page-1", "type": "text", "text": "核心结论",
                "required_edit": "native",
                "provenance": {"kind": "user", "source": "user-input.md", "checked": True, "uncertainties": []},
            })
            (task_dir / "task.json").write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
            comp = {
                "page_role": "body", "claim_content_id": "p1-title",
                "content_relation": "核心结论与支撑数据", "layout_family": "顶部断言配双列证据",
                "reading_path": ["p1-title"], "information_attachment": "mixed",
                "layer_plan": {"primary": "主结论", "secondary": "证据列", "detail": "口径备注"},
                "rationale": "先给判断再展开支撑数据。",
            }
            (task_dir / "comp-p1.json").write_text(json.dumps(comp, ensure_ascii=False), encoding="utf-8")
            (task_dir / "note-p1.txt").write_text("第1页讲稿与数据口径说明。", encoding="utf-8")

            rc, res = run_cli("set-page", "--task-dir", str(task_dir), "--page", "page-1",
                              "--notes-file", "note-p1.txt", "--composition-file", "comp-p1.json")
            self.assertEqual(rc, 0)
            self.assertEqual(set(res["updated"]), {"notes", "composition"})

            # Reorder pages and confirm both scene and design pages follow
            rc, res = run_cli("reorder-pages", "--task-dir", str(task_dir), "--pages", "page-2,page-1,page-mid")
            self.assertEqual(rc, 0)
            updated_task = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
            self.assertEqual([p["id"] for p in updated_task["scene"]["pages"]], ["page-2", "page-1", "page-mid"])
            self.assertEqual([d["page_id"] for d in updated_task["design"]["pages"]], ["page-2", "page-1", "page-mid"])

            # Remove middle page
            rc, res = run_cli("remove-page", "--task-dir", str(task_dir), "--page", "page-mid")
            self.assertEqual(rc, 0)
            self.assertEqual(res["pages"], ["page-2", "page-1"])

            # Guardrails on pure helpers
            with self.assertRaisesRegex(DesignError, "SET_META_EMPTY"):
                set_meta(updated_task)
            with self.assertRaisesRegex(DesignError, "SET_PAGE_EMPTY"):
                set_page(updated_task, "page-1")
            with self.assertRaisesRegex(DesignError, "REORDER_PAGE_SET_MISMATCH"):
                reorder_pages(updated_task, ["page-1"])
            one_page = new_task("single", mode="create", width=960, height=540, pages=1)
            with self.assertRaisesRegex(DesignError, "CANNOT_REMOVE_LAST_PAGE"):
                remove_page(one_page, "page-1")
            with self.assertRaisesRegex(DesignError, "PAGE_POSITION_CONFLICT"):
                add_page(one_page, "page-2", after="page-1", before="page-1")

            # Store still refuses symlinked task directories under sandboxed ancestor fallback.
            if os.name != "nt":
                link_dir = Path(tmp).resolve() / "link-task"
                link_dir.symlink_to(task_dir)
                rc, err = run_cli("status", "--task-dir", str(link_dir))
                self.assertEqual(rc, 1)
                self.assertIn("UNSAFE_TASK_DIRECTORY", err["error"])

    def test_installed_fonts_inventory_reports_cleanly_with_or_without_fc_list(self):
        from unittest.mock import patch
        from engine.design_scene import runtime as rt

        with patch.object(rt, "find_tool", return_value=None):
            missing = rt.installed_fonts()
            self.assertFalse(missing["available"])
            self.assertEqual(missing["reason"], "fc_list_unavailable")
        with patch.object(rt, "find_tool", return_value="/usr/bin/fc-list"), \
                patch.object(rt, "run_process", return_value="Inter\nHiragino Sans GB,冬青黑体简体中文\nArial\n"):
            found = rt.installed_fonts()
            self.assertTrue(found["available"])
            self.assertEqual(found["latin"], ["Inter", "Arial"])
            self.assertEqual(found["cjk"], ["Hiragino Sans GB"])
            self.assertIn("preflight", found["scope"])


class StructuralAndChartGuardrailTests(unittest.TestCase):
    def _add_text(self, task, page_idx, cid, text, *, x=40, y=40, size=14):
        pid = f"page-{page_idx + 1}"
        task["content"]["items"].append({
            "id": cid, "page_id": pid, "type": "text", "text": text,
            "required_edit": "native",
            "provenance": {"kind": "user", "source": "test", "checked": True, "uncertainties": []},
        })
        task["scene"]["pages"][page_idx]["nodes"].append({
            "id": f"n-{cid}", "page_id": pid, "type": "text", "role": "native_text",
            "content_id": cid, "box": {"x": x, "y": y, "width": 300, "height": 30}, "z": 0,
            "font": {"family": "Inter", "size": size, "color": "111111"},
            "align": "left", "valign": "top", "wrap": True,
        })

    def _set_role(self, task, page_idx, role, claim=None, layout="distinct"):
        comp = {
            "page_role": role, "content_relation": "r", "layout_family": f"{layout}-{page_idx}",
            "reading_path": [claim] if claim else [], "information_attachment": "mixed",
            "layer_plan": {"primary": "p", "secondary": "s", "detail": "d"}, "rationale": "ok",
        }
        if claim:
            comp["claim_content_id"] = claim
        task["design"]["pages"][page_idx]["composition"] = comp

    def test_composition_flags_section_gaps_style_drift_and_number_mismatch(self):
        from engine.design_scene.composition import composition_diagnostics

        task = new_task("nav-audit", mode="create", width=960, height=540, pages=6)
        # P1 cover, P2 contents (3 chapters), P3 body before first section, P4 section 01 (dark),
        # P5 body with eyebrow 02, P6 section 02 (light)
        self._add_text(task, 0, "p1-t", "封面", y=120, size=32)
        self._set_role(task, 0, "cover")
        for idx, num in enumerate(("01", "02", "03")):
            self._add_text(task, 1, f"p2-c{idx}", num, y=100 + idx * 80, size=24)
        self._set_role(task, 1, "contents")
        self._add_text(task, 2, "p3-eb", "01 总览", y=24, size=9)
        self._add_text(task, 2, "p3-t", "总览结论", y=44, size=18)
        self._set_role(task, 2, "body", claim="p3-t")
        task["scene"]["pages"][3]["background"] = "#051C2C"
        self._add_text(task, 3, "p4-n", "01", y=110, size=56)
        self._set_role(task, 3, "section")
        self._add_text(task, 4, "p5-eb", "02 AI 变革", y=24, size=9)
        self._add_text(task, 4, "p5-t", "AI 结论", y=44, size=18)
        self._set_role(task, 4, "body", claim="p5-t")
        task["scene"]["pages"][5]["background"] = "#F4F6F9"
        self._add_text(task, 5, "p6-n", "02", y=110, size=56)
        self._set_role(task, 5, "section")

        codes = {w["code"] for w in composition_diagnostics(task)["warnings"]}
        self.assertIn("SECTION_STYLE_INCONSISTENT", codes)
        self.assertIn("SECTION_LEAD_IN_MISSING", codes)
        self.assertIn("SECTION_COUNT_MISMATCH", codes)
        self.assertIn("SECTION_NUMBER_MISMATCH", codes)

    def test_composition_passes_when_toc_sections_and_eyebrows_align(self):
        from engine.design_scene.composition import composition_diagnostics

        task = new_task("nav-clean", mode="create", width=960, height=540, pages=6)
        self._set_role(task, 0, "cover")
        self._add_text(task, 1, "p2-c1", "01", y=100, size=24)
        self._add_text(task, 1, "p2-c2", "02", y=180, size=24)
        self._set_role(task, 1, "contents")
        task["scene"]["pages"][2]["background"] = "#051C2C"
        self._add_text(task, 2, "p3-n", "01", y=110, size=56)
        self._set_role(task, 2, "section")
        self._add_text(task, 3, "p4-eb", "01 总览", y=24, size=9)
        self._add_text(task, 3, "p4-t", "总览结论", y=44, size=18)
        self._set_role(task, 3, "body", claim="p4-t")
        task["scene"]["pages"][4]["background"] = "#051C2C"
        self._add_text(task, 4, "p5-n", "02", y=110, size=56)
        self._set_role(task, 4, "section")
        self._add_text(task, 5, "p6-eb", "02 深入", y=24, size=9)
        self._add_text(task, 5, "p6-t", "深入结论", y=44, size=18)
        self._set_role(task, 5, "body", claim="p6-t")

        codes = {w["code"] for w in composition_diagnostics(task)["warnings"]}
        self.assertFalse(codes & {
            "SECTION_STYLE_INCONSISTENT", "SECTION_LEAD_IN_MISSING",
            "SECTION_COUNT_MISMATCH", "SECTION_NUMBER_MISMATCH",
        })

    def test_lint_blocks_mixed_unit_single_axis_chart_and_allows_uniform_units(self):
        canvas = {"width": 960, "height": 540}
        mixed = {"items": [{
            "kind": "chart", "x": 40, "y": 100, "w": 400, "h": 200,
            "spec": {
                "type": "column",
                "categories": ["2025 用电 (GW)", "2030 用电 (GW)", "2022 占比 (%)", "2030 占比 (%)"],
                "series": [{"name": "数值", "values": [30, 90, 3, 14]}],
            },
        }]}
        res_mixed = lint(mixed, canvas)
        self.assertEqual(res_mixed["errors"], 1)
        self.assertIn("CHART_MIXED_UNITS", {f["code"] for f in res_mixed["findings"]})

        uniform = {"items": [{
            "kind": "chart", "x": 40, "y": 100, "w": 400, "h": 200,
            "spec": {
                "type": "column",
                "categories": ["2025 用电 (GW)", "2030 用电 (GW)"],
                "series": [{"name": "电力需求 (GW)", "values": [30, 90]}],
            },
        }]}
        res_ok = lint(uniform, canvas)
        self.assertEqual(res_ok["errors"], 0)


if __name__ == "__main__":
    unittest.main()

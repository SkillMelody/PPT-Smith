#!/usr/bin/env python3
"""Focused read-only composition diagnostics regressions; no Office dependency."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.design_scene.composition import composition_diagnostics
from engine.design_scene.contract import validate


def task_for(roles):
    task = {
        "schema_version": "1.0", "task_id": "diagnostic-test", "author_id": "test",
        "mode": "create", "audience": "reviewers", "language": "en", "target_software": "LibreOffice",
        "canvas": {"width": 960, "height": 540, "unit": "pt"},
        "content": {"items": [], "notes": []},
        "design": {"brief": "Diagnostics fixture", "references": [], "pages": [], "revision_budget": 1},
        "scene": {"pages": []}, "assets": {"items": []},
    }
    for number, role in enumerate(roles, 1):
        pid, cid = f"page-{number}", f"claim-{number}"
        task["content"]["items"].append({
            "id": cid, "page_id": pid, "type": "text", "text": "Evidence-based claim",
            "required_edit": "native", "provenance": {
                "kind": "user", "source": "fixture", "checked": True, "uncertainties": []},
        })
        task["content"]["notes"].append({"page_id": pid, "text": "Fixture speaker note."})
        design = {"page_id": pid, "quality_limits": [], "accepted_differences": [],
                  "aspect_policy": "exact", "raster_acceptances": []}
        if role is not None:
            design["composition"] = {
                "page_role": role, "claim_content_id": cid, "content_relation": "Evidence and conclusion",
                "layout_family": "comparison", "reading_path": [cid], "information_attachment": "mixed",
                "layer_plan": {"primary": "claim", "secondary": "evidence", "detail": "source"},
                "rationale": "A comparison exposes the relationship.",
            }
        task["design"]["pages"].append(design)
        task["scene"]["pages"].append({"id": pid, "background": "FFFFFF", "nodes": [{
            "id": f"title-{number}", "page_id": pid, "type": "text", "role": "native_text",
            "content_id": cid, "box": {"x": 40, "y": 50, "width": 800, "height": 48}, "z": 1,
            "font": {"family": "Arial", "size": 28, "color": "20252B", "bold": True},
            "align": "left", "valign": "top", "wrap": True,
        }]})
    return task


class CompositionDiagnosticsTest(unittest.TestCase):
    def test_nested_groups_report_absolute_boxes_and_font_overrides(self):
        task = task_for(["body", "body"])
        title = task["scene"]["pages"][0]["nodes"][0]
        title["box"] = {"x": 5, "y": 7, "width": 700, "height": 48}
        title["spans"] = [{"start": 0, "end": 8, "font": {
            "family": "Arial", "size": 30, "color": "FF6900"}}]
        inner = {"id": "inner", "page_id": "page-1", "type": "group", "role": "group", "z": 1,
                 "box": {"x": 15, "y": 13, "width": 750, "height": 100}, "children": [title]}
        outer = {"id": "outer", "page_id": "page-1", "type": "group", "role": "group", "z": 1,
                 "box": {"x": 20, "y": 30, "width": 800, "height": 200}, "children": [inner]}
        task["scene"]["pages"][0]["nodes"] = [outer]
        validate(task, complete=True)
        report = composition_diagnostics(task)
        node = report["body_claim_observations"][0]["nodes"][0]
        self.assertEqual(node["absolute_box"], {"x": 40, "y": 50, "width": 700, "height": 48})
        self.assertEqual(node["font"]["size"], 28)
        self.assertEqual(node["spans"][0]["font"]["size"], 30)
        self.assertEqual(report["body_claim_anchor_patterns"][0]["page_ids"], ["page-1", "page-2"])

    def test_incomplete_or_nontext_claims_are_reported_without_guessing_titles(self):
        task = task_for(["body"] * 5)
        del task["design"]["pages"][0]["composition"]["claim_content_id"]
        task["design"]["pages"][1]["composition"]["claim_content_id"] = "absent"
        task["content"]["items"][2]["type"] = "table"
        task["scene"]["pages"][3]["nodes"][0]["type"] = "image"
        second = copy.deepcopy(task["scene"]["pages"][4]["nodes"][0])
        second["id"] = "duplicate-binding"
        second["box"]["x"] = 45
        task["scene"]["pages"][4]["nodes"].append(second)
        report = composition_diagnostics(task)
        self.assertEqual([item["status"] for item in report["body_claim_observations"]], [
            "missing_claim_reference", "missing_content", "non_text_content", "no_native_text_node",
            "multiple_native_text_nodes"])
        self.assertEqual(len(report["body_claim_observations"][-1]["nodes"]), 2)

    def test_navigation_is_visible_in_sequence_and_exempt_from_anchor_comparison(self):
        task = task_for(["cover", "contents", "section", "body", "closing", None])
        for number, page in enumerate(task["scene"]["pages"]):
            page["nodes"][0]["box"]["y"] = 100 + number * 20
        report = composition_diagnostics(task)
        self.assertEqual([item["page_id"] for item in report["body_claim_observations"]], ["page-4"])
        self.assertEqual(report["navigation_inventory"]["page_ids_by_role"], {
            "cover": ["page-1"], "contents": ["page-2"], "section": ["page-3"], "body": ["page-4"],
            "closing": ["page-5"], "unplanned": ["page-6"]})
        self.assertEqual([row["page_number"] for row in report["pages"]], [1, 2, 3, 4, 5, 6])
        self.assertIsNone(report["pages"][1]["latest_section_page_id"])
        self.assertEqual(report["pages"][2]["latest_section_page_id"], "page-3")
        self.assertEqual(report["pages"][3]["latest_section_page_id"], "page-3")
        self.assertEqual(report["warnings"], [])

    def test_exact_anchor_patterns_expose_position_font_and_alignment_changes(self):
        task = task_for(["body"] * 6)
        nodes = [page["nodes"][0] for page in task["scene"]["pages"]]
        nodes[1]["box"]["x"] += .1
        nodes[2]["box"]["y"] += 10
        nodes[3]["font"]["size"] += 1
        nodes[4]["font"]["family"] = "Liberation Sans"
        nodes[5]["align"] = "center"
        report = composition_diagnostics(task)
        self.assertEqual(len(report["body_claim_anchor_patterns"]), 6)
        self.assertEqual({w["code"] for w in report["warnings"]},
                         {"COMPOSITION_REPEATED_SEQUENCE", "COMPOSITION_DOMINANT_FAMILY"})
        self.assertFalse(report["automatic_visual_approval"])
        self.assertEqual(report["status"], "diagnostic_only")

    def test_old_unplanned_task_still_valid_and_navigation_is_not_required(self):
        task = task_for([None, None])
        self.assertEqual(validate(task, complete=True)["status"], "valid")
        report = composition_diagnostics(task)
        self.assertEqual(report["unplanned_page_ids"], ["page-1", "page-2"])
        self.assertEqual(report["body_claim_observations"], [])
        self.assertEqual(report["body_claim_anchor_patterns"], [])
        self.assertEqual(report["warnings"], [])

    def test_existing_repetition_rules_and_navigation_breaks_are_unchanged(self):
        task = task_for(["body", "body", "section", "body", "body", "body", None])
        task["design"]["review_profile"] = "decorative_business"
        report = composition_diagnostics(task)
        warnings = {item["code"]: item["page_ids"] for item in report["warnings"]}
        self.assertEqual(warnings, {
            "COMPOSITION_PLAN_INCOMPLETE": ["page-7"],
            "COMPOSITION_REPEATED_SEQUENCE": ["page-4", "page-5", "page-6"],
            "COMPOSITION_DOMINANT_FAMILY": ["page-1", "page-2", "page-4", "page-5", "page-6"],
        })

    def test_diagnostics_do_not_mutate_task(self):
        task = task_for(["body", "section", "body", None])
        before = copy.deepcopy(task)
        composition_diagnostics(task)
        self.assertEqual(task, before)


if __name__ == "__main__":
    unittest.main(verbosity=2)

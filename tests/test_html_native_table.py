"""Check merged-cell geometry, rich text and edge styles in the editable PPTX."""
import io

import pytest
from pptx import Presentation

from engine.design_scene import html_import as hi
from engine.design_scene.backend import A, inspect_objects, render
from engine.design_scene.contract import validate
from engine.design_scene.pipeline import new_task
from engine.design_scene.preflight import font_samples
from engine.design_scene.store import DesignError


def cell(text, x, width, **kwargs):
    style = {"size": 14, "stack": ["Arial"], "color": "rgb(0,0,0)", "weight": 400,
             "italic": False, "lineHeight": 18, "letterSpacing": 0}
    return {"x": x, "w": width, "font": style, "runs": [{"text": text, **style}], "pad": [2] * 4,
            "align": "left", "valign": "middle", "fill": None, **kwargs}


def merged_task():
    task = new_task("merged-table", mode="create", width=960, height=540, pages=1, author="test")
    task["design"]["brief"] = "Editable table"
    task["content"]["notes"].append({"page_id": "page-1", "text": "fixture"})
    origin = cell("A", 0, 160, rowSpan=2, colSpan=2)
    origin["runs"].append({**origin["font"], "text": "B", "stack": ["Test Face"], "weight": 700, "color": "rgb(171,18,52)"})
    origin["borders"] = {side: {"w": i, "c": "rgb(35,69,103)"} for i, side in enumerate(("left", "right", "top", "bottom"), 1)}
    rows = [[origin, cell("C", 160, 80)], [cell("D", 160, 80)],
            [cell("L", 0, 100), cell("M", 100, 60), cell("N", 160, 80)]]
    table = {"kind": "table", "cid": "records", "x": 0, "y": 10, "w": 240, "h": 90,
             "rows": [{"h": 30, "cells": row} for row in rows]}
    layout = {"background": "rgb(255,255,255)", "items": [table]}
    items, nodes, bg, *_ = hi.to_scene(layout, "page-1", task["canvas"], default_source="fixture")
    items[0]["provenance"]["checked"] = True
    return hi.apply(task, "page-1", items, nodes, bg)[0]


def test_native_table_merge_edges_and_rich_runs():
    task = merged_task()
    data = render(task, {})
    inspect_objects(data, task)
    table = Presentation(io.BytesIO(data)).slides[0].shapes[0].table
    assert [column.width.pt for column in table.columns] == [100, 60, 80]
    origin = table.cell(0, 0)
    assert (origin.span_height, origin.span_width) == (2, 2)
    assert table.cell(1, 1).is_spanned
    assert table.cell(1, 2).text == "D"
    runs = origin.text_frame.paragraphs[0].runs
    assert [(run.text, run.font.bold, str(run.font.color.rgb)) for run in runs] == [
        ("A", False, "000000"), ("B", True, "AB1234")]
    assert any(s["family"] == "Test Face" and s["text"] == "B" and s["bold"] for s in font_samples(task))
    for i, tag in enumerate(("lnL", "lnR", "lnT", "lnB"), 1):
        line = origin._tc.tcPr.find(A + tag)
        assert int(line.get("w")) == i * 12700
        assert line.find(A + "solidFill/" + A + "srgbClr").get("val") == "234567"


def test_invalid_merge_and_span_are_rejected():
    task = merged_task()
    style = task["scene"]["pages"][0]["nodes"][0]["cell_styles"][0][0]
    style["row_span"] = 4
    with pytest.raises(DesignError, match="TABLE_MERGE_OUT_OF_BOUNDS"):
        validate(task)
    style["row_span"] = 2
    style["spans"][0]["end"] = 5
    with pytest.raises(DesignError, match="TEXT_SPAN_RANGE_INVALID"):
        validate(task)
    style["spans"] = []
    task["content"]["items"][0]["cells"][1][1] = "must remain visible"
    with pytest.raises(DesignError, match="TABLE_MERGED_CELL_MUST_BE_EMPTY"):
        validate(task)

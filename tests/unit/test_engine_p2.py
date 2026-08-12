from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from engine.coverage import coverage_report
from engine.extractive_ir import build_extractive_ir
from engine.provenance import verify_ir
from engine.structural_parser import parse_html, parse_markdown

ROOT = Path(__file__).resolve().parents[2]
IR_SCHEMA = json.loads((ROOT / "schemas/v4/presentation-ir.schema.json").read_text("utf-8"))

MD = """# 2025 年度经营总结

前言段落，介绍背景。

## 收入与增长

2025 年销售收入增长 36%，其中海外业务贡献最大。

- 海外业务收入 +52%
- 国内业务收入 +8%

| 区域 | 收入 | 同比 |
| --- | --- | --- |
| 海外 | 120 | +52% |
| 国内 | 300 | +8% |

## 风险

毛利率下降 2.8 个百分点。

> 管理层认为价格策略是主因。

![增长趋势图](assets/trend.png)
"""

HTML = """<html><body>
<h1>年度总结</h1>
<p>前言。</p>
<h2>业绩</h2>
<p>收入增长 36%。</p>
<ul><li>海外 +52%</li><li>国内 +8%</li></ul>
<table><tr><th>区域</th><th>同比</th></tr><tr><td>海外</td><td>+52%</td></tr></table>
<script>ignored()</script>
</body></html>"""


def _doc():
    return parse_markdown(MD, "src")


def test_markdown_parser_anchors_and_types():
    doc = _doc()
    types = [(e.etype, e.anchor) for e in doc.elements]
    assert ("h1", "h1_1") in types
    assert ("h2", "h2_1") in types and ("h2", "h2_2") in types
    assert ("table", "table_1") in types
    assert ("list", "list_1") in types
    assert ("blockquote", "blockquote_1") in types
    assert ("img", "img_1") in types
    table = doc.get("table_1")
    assert table.rows[0] == ["区域", "收入", "同比"]
    assert doc.get("list_1").items == ["海外业务收入 +52%", "国内业务收入 +8%"]
    assert "36%" in doc.get("para_2").numbers()


def test_html_parser_anchors_and_script_skipped():
    doc = parse_html(HTML, "web")
    assert doc.title() == "年度总结"
    assert doc.get("list_1").items == ["海外 +52%", "国内 +8%"]
    assert doc.get("table_1").rows[1] == ["海外", "+52%"]
    assert all("ignored" not in e.full_text() for e in doc.elements)


def test_extractive_ir_is_schema_valid_and_anchored():
    result = build_extractive_ir(_doc(), source_meta={"type": "markdown"})
    ir = result["ir"]
    errors = list(Draft202012Validator(IR_SCHEMA).iter_errors(ir))
    assert not errors, [e.message for e in errors[:3]]
    assert ir["deck"]["title"] == "2025 年度经营总结"
    assert ir["deck"]["language"] == "zh"
    titles = [s["title"] for s in ir["slides"]]
    assert "收入与增长" in titles and "风险" in titles
    # Extractive IR must pass its own provenance check by construction.
    assert verify_ir(ir, {"src": _doc()}) == []


def test_provenance_rejects_fabrication():
    doc = _doc()
    result = build_extractive_ir(doc, source_meta={"type": "markdown"})
    ir = copy.deepcopy(result["ir"])

    # Dangling anchor
    ir["slides"][0]["blocks"][0]["source_ref"]["loc"] = "para_99"
    errors = verify_ir(ir, {"src": doc})
    assert any(e["code"] == "LOC_NOT_FOUND" for e in errors)

    # Fabricated metric number
    ir2 = copy.deepcopy(result["ir"])
    ir2["slides"][0]["blocks"].append({
        "role": "metric", "label": "利润", "value": "+99%",
        "source_ref": {"source_id": "src", "loc": "para_2"},
    })
    errors2 = verify_ir(ir2, {"src": doc})
    assert any(e["code"] == "METRIC_VALUE_NOT_IN_SOURCE" for e in errors2)

    # Real metric number passes
    ir3 = copy.deepcopy(result["ir"])
    ir3["slides"][0]["blocks"].append({
        "role": "metric", "label": "收入", "value": "+36%",
        "source_ref": {"source_id": "src", "loc": "para_2"},
    })
    assert not [e for e in verify_ir(ir3, {"src": doc})
                if e["code"] == "METRIC_VALUE_NOT_IN_SOURCE"]

    # Quote mismatch
    ir4 = copy.deepcopy(result["ir"])
    ir4["slides"][0]["blocks"][0]["source_ref"]["quote"] = "从未出现的句子"
    assert any(e["code"] == "QUOTE_MISMATCH" for e in verify_ir(ir4, {"src": doc}))

    # Table block anchored to a paragraph
    ir5 = copy.deepcopy(result["ir"])
    ir5["slides"][0]["blocks"].append({
        "role": "table", "source_ref": {"source_id": "src", "loc": "para_1"},
    })
    assert any(e["code"] == "TABLE_REF_NOT_TABLE" for e in verify_ir(ir5, {"src": doc}))


def test_coverage_flags_dropped_sections_and_tables():
    doc = _doc()
    full = build_extractive_ir(doc, source_meta={"type": "markdown"})["ir"]
    report = coverage_report(full, {"src": doc})
    assert report["status"] == "pass"
    assert report["sources"][0]["table_ratio"] == 1.0

    partial = copy.deepcopy(full)
    partial["slides"] = [s for s in partial["slides"] if s["title"] != "风险"]
    partial["slides"] = [s for s in partial["slides"]
                         if not any(b.get("role") == "table" for b in s["blocks"])] or partial["slides"][:1]
    report2 = coverage_report(partial, {"src": doc})
    assert report2["status"] in ("warn", "fail")
    assert report2["sources"][0]["sections_uncovered"]


def test_empty_document_still_produces_a_slide():
    doc = parse_markdown("", "empty")
    result = build_extractive_ir(doc, source_meta={"type": "markdown"})
    ir = result["ir"]
    assert len(ir["slides"]) == 1
    assert not list(Draft202012Validator(IR_SCHEMA).iter_errors(ir))
    assert result["warnings"]

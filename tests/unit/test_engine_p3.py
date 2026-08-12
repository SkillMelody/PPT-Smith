from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation

from engine.compile import compile_deck
from tests.unit.test_engine_p2 import MD

LLM_IR = {
    "schema_version": "4.0.0",
    "deck": {"title": "2025 年度经营回顾", "language": "zh"},
    "sources": [{"source_id": "src", "type": "markdown"}],
    "slides": [
        {
            "id": "s1", "title": "增长由海外业务驱动",
            "blocks": [
                {"role": "metric", "label": "总收入", "value": "+36%",
                 "source_ref": {"source_id": "src", "loc": "para_2"}},
                {"role": "metric", "label": "海外", "value": "+52%",
                 "source_ref": {"source_id": "src", "loc": "list_1"}},
                {"role": "risk", "text": "毛利率下降 2.8 个百分点"},
            ],
        },
        {
            "id": "s2", "title": "分区域明细",
            "blocks": [{"role": "table",
                        "source_ref": {"source_id": "src", "loc": "table_1"}}],
        },
    ],
}


def _write_article(tmp_path: Path) -> Path:
    path = tmp_path / "article.md"
    path.write_text(MD, encoding="utf-8")
    return path


def test_compile_extractive_end_to_end(tmp_path):
    article = _write_article(tmp_path)
    report = compile_deck(sources=[("src", "markdown", str(article))],
                          output_dir=str(tmp_path / "out"))
    assert report["ok"], report
    assert report["ir_origin"] == "extractive"
    assert report["qa"]["error_count"] == 0
    for name in ("deck.pptx", "render-plan.json", "decision-trace.json", "ir.json"):
        assert (tmp_path / "out" / name).is_file()
    prs = Presentation(str(tmp_path / "out" / "deck.pptx"))
    assert len(prs.slides) == report["slide_count"]


def test_compile_provided_ir_selects_archetypes(tmp_path):
    article = _write_article(tmp_path)
    ir_path = tmp_path / "ir.json"
    ir_path.write_text(json.dumps(LLM_IR, ensure_ascii=False), encoding="utf-8")
    report = compile_deck(sources=[("src", "markdown", str(article))],
                          ir_path=str(ir_path), output_dir=str(tmp_path / "out"))
    assert report["ok"] and report["ir_origin"] == "provided"
    trace = json.loads((tmp_path / "out" / "decision-trace.json").read_text("utf-8"))
    chosen = {d["slide_id"]: d["chosen"] for d in trace["decisions"]}
    assert chosen == {"s1": "kpi_wall", "s2": "full_table"}
    assert all(d["chosen_by"] == "rule" for d in trace["decisions"])


def test_invalid_ir_degrades_but_still_ships(tmp_path):
    article = _write_article(tmp_path)
    bad = json.loads(json.dumps(LLM_IR))
    bad["slides"][0]["blocks"][0]["value"] = "+99%"  # fabricated number
    ir_path = tmp_path / "bad.json"
    ir_path.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    report = compile_deck(sources=[("src", "markdown", str(article))],
                          ir_path=str(ir_path), output_dir=str(tmp_path / "out"))
    assert report["ok"]
    assert report["ir_origin"] == "extractive_fallback"
    assert any(e["code"] == "METRIC_VALUE_NOT_IN_SOURCE"
               for e in report["ir_rejection_errors"])
    assert any(d["kind"] == "extractive_ir_fallback" for d in report["degradations"])
    assert (tmp_path / "out" / "deck.pptx").is_file()


def test_invalid_ir_fails_closed_without_degrade(tmp_path):
    article = _write_article(tmp_path)
    bad = json.loads(json.dumps(LLM_IR))
    bad["slides"][0]["page_archetype"] = "kpi"  # visual field -> schema reject
    ir_path = tmp_path / "bad.json"
    ir_path.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    report = compile_deck(sources=[("src", "markdown", str(article))],
                          ir_path=str(ir_path), output_dir=str(tmp_path / "out"),
                          degrade_on_error=False)
    assert report["ok"] is False and report["stage"] == "ir_validation"
    assert not (tmp_path / "out" / "deck.pptx").exists()


def test_render_plan_is_deterministic(tmp_path):
    article = _write_article(tmp_path)
    for run in ("a", "b"):
        compile_deck(sources=[("src", "markdown", str(article))],
                     output_dir=str(tmp_path / run))
    assert (tmp_path / "a" / "render-plan.json").read_bytes() == \
           (tmp_path / "b" / "render-plan.json").read_bytes()
    assert (tmp_path / "a" / "decision-trace.json").read_bytes() == \
           (tmp_path / "b" / "decision-trace.json").read_bytes()

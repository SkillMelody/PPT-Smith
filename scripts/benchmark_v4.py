#!/usr/bin/env python3
"""Cross-model benchmark harness for the v4 acceptance metrics (P8).

Measures, per (case x IR-producer), exactly the plan §1 acceptance
numbers: pipeline walk-through rate, blank-page count, QA errors,
degradations, coverage, and per-run geometry determinism.

Case layout (a directory):
  cases/
    <case-name>/
      source.md | source.html | source.txt
      irs/                # optional; one IR file per model/producer
        <producer>.json   # e.g. glm-5.json, deepseek-v4-flash.json

Every case also always runs the `no-ir` producer (extractive route),
which is the guaranteed floor any model can reach by running compile
without an IR. Real-model IRs are produced by pointing each model at
SKILL.md and collecting the ir.json it writes; drop those files into
irs/ and re-run this harness.

Usage:
  python3 scripts/benchmark_v4.py --cases tests/fixtures/v4-bench \
      --output-dir /tmp/bench [--style styles/<pack>.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.compile import compile_deck  # noqa: E402

SOURCE_TYPES = {".md": "markdown", ".html": "html", ".txt": "text"}


def _geometry_sha(render_plan_path: Path) -> str:
    plan = json.loads(render_plan_path.read_text(encoding="utf-8"))
    plan.pop("plan", None)  # ids/hashes differ per IR; geometry is the rest
    return hashlib.sha256(
        json.dumps(plan, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]


def run_case(case_dir: Path, out_root: Path, style: str | None) -> list[dict]:
    source = next((p for p in sorted(case_dir.iterdir())
                   if p.suffix in SOURCE_TYPES), None)
    if source is None:
        return [{"case": case_dir.name, "producer": "-", "ok": False,
                 "error": "no source file"}]
    source_spec = [("doc", SOURCE_TYPES[source.suffix], str(source))]

    producers: list[tuple[str, str | None]] = [("no-ir", None)]
    irs_dir = case_dir / "irs"
    if irs_dir.is_dir():
        producers += [(p.stem, str(p)) for p in sorted(irs_dir.glob("*.json"))]

    rows = []
    for producer, ir_path in producers:
        results = []
        for attempt in ("a", "b"):  # two runs -> determinism check
            out = out_root / case_dir.name / producer / attempt
            try:
                report = compile_deck(sources=source_spec, ir_path=ir_path,
                                      style_path=style, output_dir=str(out),
                                      degrade_on_error=True)
            except Exception as exc:  # harness must survive any input
                report = {"ok": False, "crash": f"{type(exc).__name__}: {exc}"}
            results.append((out, report))

        (out, report), (out_b, report_b) = results
        qa = report.get("qa", {})
        blank = sum(1 for e in qa.get("errors", []) if e.get("code") == "SLIDE_EMPTY")
        deterministic = None
        plan_a, plan_b = out / "render-plan.json", out_b / "render-plan.json"
        if plan_a.is_file() and plan_b.is_file():
            deterministic = _geometry_sha(plan_a) == _geometry_sha(plan_b)
        coverage = report.get("coverage", {})
        worst_section = min((s["section_ratio"]
                             for s in coverage.get("sources", [])), default=None)
        rows.append({
            "case": case_dir.name,
            "producer": producer,
            "ok": bool(report.get("ok")),
            "crash": report.get("crash"),
            "ir_origin": report.get("ir_origin"),
            "ir_rejected": report.get("ir_origin") == "extractive_fallback",
            "qa_errors": qa.get("error_count"),
            "blank_slides": blank,
            "slide_count": report.get("slide_count"),
            "degradation_count": len(report.get("degradations", [])),
            "coverage_status": coverage.get("status"),
            "worst_section_ratio": worst_section,
            "deterministic": deterministic,
        })
    return rows


def summarize(rows: list[dict]) -> dict:
    producers = sorted({r["producer"] for r in rows})
    summary = {}
    for producer in producers:
        mine = [r for r in rows if r["producer"] == producer]
        summary[producer] = {
            "cases": len(mine),
            "walkthrough_rate": sum(1 for r in mine if r["ok"]) / len(mine),
            "blank_slides_total": sum(r["blank_slides"] or 0 for r in mine),
            "qa_errors_total": sum(r["qa_errors"] or 0 for r in mine),
            "ir_rejected": sum(1 for r in mine if r["ir_rejected"]),
            "deterministic": all(r["deterministic"] in (True, None) for r in mine),
        }
    return summary


def to_markdown(rows: list[dict], summary: dict) -> str:
    lines = ["# PPT Smith v4 benchmark report", "",
             "| case | producer | ok | ir_origin | qa_err | blank | slides | degr | coverage | determ |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(
            f"| {r['case']} | {r['producer']} | {'✅' if r['ok'] else '❌'} "
            f"| {r['ir_origin']} | {r['qa_errors']} | {r['blank_slides']} "
            f"| {r['slide_count']} | {r['degradation_count']} "
            f"| {r['coverage_status']} | "
            f"{'✅' if r['deterministic'] else '—' if r['deterministic'] is None else '❌'} |")
    lines += ["", "## Per-producer summary", "",
              "| producer | walk-through | blank slides | qa errors | IR rejected | deterministic |",
              "|---|---|---|---|---|---|"]
    for producer, s in summary.items():
        lines.append(f"| {producer} | {s['walkthrough_rate']:.0%} "
                     f"| {s['blank_slides_total']} | {s['qa_errors_total']} "
                     f"| {s['ir_rejected']} | {'✅' if s['deterministic'] else '❌'} |")
    lines += ["", "Acceptance floors (plan §1.3): walk-through 100%, blank slides 0, "
              "qa errors 0, deterministic ✅ for every producer. `ir_rejected` is not "
              "a failure — it proves the provenance gate + extractive fallback."]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--style")
    args = parser.parse_args()

    cases_root = Path(args.cases)
    out_root = Path(args.output_dir)
    rows: list[dict] = []
    for case_dir in sorted(p for p in cases_root.iterdir() if p.is_dir()):
        rows.extend(run_case(case_dir, out_root, args.style))
    summary = summarize(rows)

    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "benchmark-report.json").write_text(
        json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    markdown = to_markdown(rows, summary)
    (out_root / "benchmark-report.md").write_text(markdown, encoding="utf-8")
    print(markdown)

    floors_ok = all(
        s["walkthrough_rate"] == 1.0 and s["blank_slides_total"] == 0
        and s["qa_errors_total"] == 0 and s["deterministic"]
        for s in summary.values())
    return 0 if floors_ok else 1


if __name__ == "__main__":
    sys.exit(main())

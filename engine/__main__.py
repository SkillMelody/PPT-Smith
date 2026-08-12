"""Engine CLI.

Usage:
  python3 -m engine compile    --source id:type:path [--ir IR.json]
                               [--style PACK.json] --output-dir DIR
                               [--no-degrade]
  python3 -m engine parse      --source id:type:path [--json-out FILE]
  python3 -m engine extract-ir --source id:type:path [--json-out FILE]
  python3 -m engine verify     --ir IR.json --source id:type:path [...]
  python3 -m engine coverage   --ir IR.json --source id:type:path [...]

`compile` is the single entry (D2): parse -> validate/provenance ->
policy -> layout -> QA -> deck.pptx + render-plan + decision-trace.
The other subcommands expose individual stages for debugging and repair
loops. `--source` takes `source_id:type:path` (type markdown|html|text)
and may repeat. Exit codes: 0 ok, 1 findings/failure, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .coverage import coverage_report
from .extractive_ir import build_extractive_ir
from .provenance import verify_ir
from .structural_parser import parse_source


def _load_sources(specs: list[str]) -> tuple[dict, dict]:
    docs, meta = {}, {}
    for spec in specs:
        parts = spec.split(":", 2)
        if len(parts) != 3:
            raise SystemExit(f"--source expects source_id:type:path, got '{spec}'")
        source_id, source_type, path = parts
        text = Path(path).read_text(encoding="utf-8")
        docs[source_id] = parse_source(text, source_type, source_id)
        meta[source_id] = {"type": source_type, "path": path}
    return docs, meta


def _emit(payload: dict, json_out: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if json_out:
        Path(json_out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="engine", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("parse", "extract-ir", "verify", "coverage"):
        p = sub.add_parser(name)
        p.add_argument("--source", action="append", required=True,
                       metavar="ID:TYPE:PATH")
        p.add_argument("--json-out")
        if name in ("verify", "coverage"):
            p.add_argument("--ir", required=True)

    c = sub.add_parser("compile")
    c.add_argument("--source", action="append", required=True, metavar="ID:TYPE:PATH")
    c.add_argument("--ir")
    c.add_argument("--style")
    c.add_argument("--output-dir", required=True)
    c.add_argument("--no-degrade", action="store_true",
                   help="fail on invalid IR instead of falling back to extraction")

    args = parser.parse_args(argv)

    if args.command == "compile":
        from .compile import compile_deck
        specs = []
        for spec in args.source:
            parts = spec.split(":", 2)
            if len(parts) != 3:
                print(f"error: --source expects source_id:type:path, got '{spec}'",
                      file=sys.stderr)
                return 2
            specs.append(tuple(parts))
        report = compile_deck(sources=specs, ir_path=args.ir, style_path=args.style,
                              output_dir=args.output_dir,
                              degrade_on_error=not args.no_degrade)
        print(json.dumps({k: report[k] for k in
                          ("ok", "ir_origin", "slide_count", "pptx", "stage")
                          if k in report}, ensure_ascii=False, indent=2))
        return 0 if report.get("ok") else 1
    try:
        docs, meta = _load_sources(args.source)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.command == "parse":
        _emit({"documents": [doc.to_dict() for doc in docs.values()]}, args.json_out)
        return 0

    if args.command == "extract-ir":
        if len(docs) != 1:
            print("error: extract-ir expects exactly one --source", file=sys.stderr)
            return 2
        (source_id, doc), = docs.items()
        result = build_extractive_ir(doc, source_meta=meta[source_id])
        _emit(result, args.json_out)
        return 0

    ir = json.loads(Path(args.ir).read_text(encoding="utf-8"))
    if args.command == "verify":
        errors = verify_ir(ir, docs)
        _emit({"ok": not errors, "error_count": len(errors), "errors": errors},
              args.json_out)
        return 1 if errors else 0

    report = coverage_report(ir, docs)
    _emit(report, args.json_out)
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())

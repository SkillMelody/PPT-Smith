#!/usr/bin/env python3
"""P12-refine Level 2: code-level refine entry (v3 Path A's freedom, with QA net).

`engine refine-code` runs a user/model-written python-pptx build script that
refines a slide (or builds a whole deck) with full layout freedom, then runs
the ppt_qa structural inspection as a safety net. If inspection finds fatal
issues the refine is REJECTED and the caller keeps the engine deck — a
refine must never ship something QA would block.

Script contract:
  - define ``build(prs, context) -> None``: mutate the Presentation in place
  - ``context`` carries {"source_path", "ir_path", "output_dir", "slide_ids"}
  - the script may import python-pptx and the skill's builders/ helpers

CLI:
  python3 -m engine refine-code --script refine_cover.py \
      --source doc:markdown:source.md --ir ir.json --output-dir out/
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ppt_qa.verifier import run_structural_inspection  # noqa: E402


def _load_script(path: Path):
    spec = importlib.util.spec_from_file_location("refine_script", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load refine script: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "build"):
        raise SystemExit(
            f"refine script must define build(prs, context) -> None; got {path}")
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", required=True, help="python-pptx refine script")
    parser.add_argument("--source", action="append", required=True,
                        metavar="ID:TYPE:PATH")
    parser.add_argument("--ir", required=True, help="Presentation IR (v4)")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--deck", help="optional: refine an existing deck.pptx "
                                       "instead of building from IR")
    args = parser.parse_args(argv)

    from pptx import Presentation

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    script = _load_script(Path(args.script))

    ir = json.loads(Path(args.ir).read_text(encoding="utf-8"))
    slide_ids = [s["id"] for s in ir.get("slides", [])]
    source_paths = {spec.split(":", 2)[0]: spec.split(":", 2)[2]
                    for spec in args.source}

    if args.deck:
        deck_path = Path(args.deck)
    else:
        # build the base deck with the engine first (deterministic floor)
        from engine.compile import compile_deck  # noqa: PLC0415
        specs = []
        for spec in args.source:
            parts = spec.split(":", 2)
            if len(parts) != 3:
                print(f"error: --source expects id:type:path, got '{spec}'",
                      file=sys.stderr)
                return 2
            specs.append(tuple(parts))
        report = compile_deck(sources=specs, ir_path=args.ir,
                              output_dir=str(out / "base"))
        if not report.get("ok"):
            print(json.dumps({"ok": False, "stage": report.get("stage"),
                              "errors": report.get("errors", [])},
                             ensure_ascii=False, indent=2))
            return 1
        deck_path = Path(report["pptx"])

    # refine: run the script on a copy so a bad refine can't corrupt the base
    refined = out / "deck-refined.pptx"
    prs = Presentation(str(deck_path))
    context = {
        "source_path": source_paths,
        "ir_path": str(Path(args.ir)),
        "output_dir": str(out),
        "slide_ids": slide_ids,
        "base_deck": str(deck_path),
    }
    script.build(prs, context)
    prs.save(str(refined))

    # QA safety net: structural inspection must find no NEW fatal/error
    # issues vs the engine base deck. Base deck issues are engine-known and
    # already accepted; a refine is rejected only if it introduces new
    # blockers (out-of-bounds, orphan blocks, blank slides, ...).
    def _blockers(pptx_path: Path) -> list[dict]:
        inspection = run_structural_inspection(pptx_path, ppt_ir=ir)
        return [i for i in inspection.get("issues", [])
                if i.get("severity") in ("fatal", "error")]

    base_blockers = _blockers(deck_path)
    refined_blockers = _blockers(refined)
    base_keys = {(b.get("code"), b.get("slide_id"), b.get("message"))
                 for b in base_blockers}
    new_blockers = [b for b in refined_blockers
                    if (b.get("code"), b.get("slide_id"), b.get("message"))
                    not in base_keys]
    result = {
        "ok": not new_blockers,
        "refined_deck": str(refined),
        "base_deck": str(deck_path),
        "inspection": {
            "base_blocker_count": len(base_blockers),
            "refined_blocker_count": len(refined_blockers),
            "new_blocker_count": len(new_blockers),
            "new_blockers": new_blockers[:8],
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

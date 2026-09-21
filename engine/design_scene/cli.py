"""Public CLI for declarative design tasks. See references/declarative-design.md."""
from __future__ import annotations

import argparse
import json
import sys

from .contract import SCHEMA, validate
from .pipeline import (REVIEW_SCHEMA, assess, build, build_prefix, deliver, image_request,
                       ingest, new_task, read_assets, review_skeleton, verify_build)
from .runtime import execution_capabilities, find_tool, renderer_identity
from .store import DesignError, Store, external_bytes, parse_json


def main(argv=None):
    parser = argparse.ArgumentParser(prog="engine design", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    schema = sub.add_parser("schema", help="print strict task or review JSON Schema")
    schema.add_argument("--review", action="store_true")
    sub.add_parser("capabilities", help="report installed backend; no fabricated tool availability")
    init = sub.add_parser("init")
    init.add_argument("--task-dir", required=True)
    init.add_argument("--task-id", required=True)
    init.add_argument("--mode", choices=["recreate", "style_transfer", "new_design", "draft", "template"], required=True)
    init.add_argument("--width", type=float, required=True, help="canvas width in points")
    init.add_argument("--height", type=float, required=True, help="canvas height in points")
    init.add_argument("--pages", type=int, default=1)
    init.add_argument("--author", default="host-model")
    init.add_argument("--audience", default="待填写")
    init.add_argument("--target-software", default="LibreOffice")
    for command in ("ingest", "crop", "validate", "image-request", "build", "status", "review-template", "review", "deliver"):
        p = sub.add_parser(command)
        p.add_argument("--task-dir", required=True)
        if command in {"ingest", "crop"}:
            p.add_argument("--asset-id", required=True)
            p.add_argument("--pages", required=True, help="comma-separated page ids")
            p.add_argument("--role", required=True, choices=["reference", "target", "photo", "illustration", "raster_data"])
            p.add_argument("--source", required=True, help="provenance description, not a private filesystem path")
            p.add_argument("--source-crop", nargs=4, type=int, metavar=("X", "Y", "W", "H"))
            if command == "ingest":
                p.add_argument("--file", required=True)
                p.add_argument("--tool-result", help="actual host tool receipt JSON; absent information must be null")
            else:
                p.add_argument("--from-asset", required=True)
        if command == "validate":
            p.add_argument("--complete", action="store_true")
        if command == "build":
            p.add_argument("--isolation", choices=["auto", "macos", "host"], default="auto",
                           help="auto selects available macOS isolation, otherwise local host execution")
            p.add_argument("--no-preview", action="store_true")
            p.add_argument("--parent-build")
        if command in {"status", "review-template", "review", "deliver"}:
            p.add_argument("--build-id", required=True)
        if command in {"review", "deliver"}:
            p.add_argument("--review-file", required=True, help="task-relative JSON file")
        if command in {"build", "review", "deliver"}:
            p.add_argument("--require-os-isolation", action="store_true",
                           help="require verified OS isolation in addition to PPT quality acceptance")
    args = parser.parse_args(argv)
    try:
        if args.command == "schema":
            result = REVIEW_SCHEMA if args.review else SCHEMA
        elif args.command == "capabilities":
            result = {"backend": renderer_identity(), "image_generation": "host_tool_required_when_needed",
                      "reference_analysis": "host_multimodal_model_required",
                      "render": {x: bool(find_tool(x)) for x in ("soffice", "pdftoppm", "fc-match", "sandbox-exec")},
                      "execution": execution_capabilities(),
                      "template": "separate_preservation_route", "automatic_visual_approval": False}
        elif args.command == "init":
            if args.mode == "template":
                raise DesignError("TEMPLATE_ROUTE_REQUIRED: see docs/v4-template-route.md")
            task = new_task(args.task_id, mode=args.mode, width=args.width, height=args.height,
                            pages=args.pages, author=args.author, audience=args.audience, target_software=args.target_software)
            with Store(args.task_dir, create=True) as store:
                store.put_json("task.json", task, exclusive=True)
            result = {"status": "preparation_required", "task_id": args.task_id,
                      "next": "Read current references, lock visible content, and establish page-specific design targets."}
        elif args.command == "build":
            result = build(args.task_dir, isolation=args.isolation, preview=not args.no_preview,
                           parent_build=args.parent_build, require_os_isolation=args.require_os_isolation)
        else:
            with Store(args.task_dir) as store:
                task = store.json("task.json")
                if args.command in {"ingest", "crop"}:
                    if args.command == "ingest":
                        data = external_bytes(args.file)
                        receipt = parse_json(external_bytes(args.tool_result, 65536)) if args.tool_result else None
                    else:
                        validate(task)
                        data = read_assets(store, task).get(args.from_asset)
                        if data is None or args.source_crop is None:
                            raise DesignError("REGISTERED_SOURCE_AND_CROP_REQUIRED")
                        receipt = None
                    result = ingest(store, task, asset_id=args.asset_id, data=data,
                                    page_ids=args.pages.split(","), role=args.role, source=args.source,
                                    crop=args.source_crop, tool_result=receipt)
                elif args.command == "validate":
                    result = validate(task, complete=args.complete)
                    read_assets(store, task)
                elif args.command == "image-request":
                    result = image_request(task)
                    store.put_json("image-request.json", result)
                elif args.command == "status":
                    _, m = verify_build(store, args.build_id)
                    result = {"status": m["status"], "build_id": args.build_id,
                              "render": m["render"]["status"], "isolation": m["isolation"],
                              "delivery_policy": m.get("delivery_policy", {"require_os_isolation": True}),
                              "review": "not_implied_by_build"}
                elif args.command == "review-template":
                    result = review_skeleton(store, args.build_id)
                    store.put_json("review-draft.json", result, exclusive=True)
                else:
                    review = store.json(args.review_file)
                    operation = deliver if args.command == "deliver" else assess
                    result = operation(store, args.build_id, review, require_os_isolation=args.require_os_isolation)
                    if args.command == "review":
                        import uuid
                        store.put_json("reviews/" + args.build_id + "-" + uuid.uuid4().hex + ".json",
                                       {"assessment": result, "review": review}, exclusive=True)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get("status") in {"build_failed", "render_incomplete", "revision_required"} else 0
    except (DesignError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())

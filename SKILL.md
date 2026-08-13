---
name: "article-html-to-ppt"
description: "Compile articles (Markdown/HTML/text) into professional, editable PPTX decks via a deterministic local engine. The model's only job: optionally write a content-only Presentation IR, then run one command. Layout, styling, and QA are engine-owned."
metadata:
  display_name: "MeowClaw PPT Smith"
  english_alias: "MeowClaw PPTSmith"
  public_slug: "meowclaw-pptsmith"
  version: "4.1.0-alpha"
  compatibility_aliases: ["article-html-to-ppt", "meowclaw-decksmith"]
---

# MeowClaw PPT Smith v4 — Model-Agnostic Presentation Compiler

Turn an article into a deck by doing exactly two things:

1. (Recommended) Write a **Presentation IR** — a content-only JSON describing what each slide says.
2. Run **one command**. The engine does everything visual: archetype selection, layout, styling, text fitting, QA, and the PPTX build — deterministically.

You never make design decisions. Do not write layout, colors, fonts, coordinates, or archetype names anywhere. The IR schema rejects them.

## Capability and permission boundary

- Read only the source files and this skill's own files; write only inside the output directory you choose.
- The engine runs locally, stdlib + python-pptx only, no network. Never upload content anywhere without explicit user consent.
- Requires `python3` (3.9+) and `python-pptx`. Optional: LibreOffice for PDF preview.

## The protocol

All commands run from this skill's root directory.

### Step 1 — Stage the source

Save the article as a file (UTF-8): `source.md`, `source.html`, or `source.txt`.

### Step 2 — See the anchors

```bash
python3 -m engine parse --source doc:markdown:source.md --json-out parsed.json
```

This prints every element with its **anchor**: `para_12`, `h2_3`, `list_1`, `table_2`, `img_1`, `blockquote_1`. Anchors are the only valid values for `source_ref.loc` in your IR. Types: `markdown`, `html`, `text`.

### Step 3 — Write the IR (skip to Step 4 to ship without it)

Contract: `schemas/v4/presentation-ir.schema.json`. Full examples: `schemas/v4/examples/presentation-ir-minimal.json` (the floor) and `presentation-ir-enriched.json` (metrics, relations, hints).

Minimal shape:

```json
{
  "schema_version": "4.0.0",
  "deck": {"title": "…", "language": "zh"},
  "sources": [{"source_id": "doc", "type": "markdown", "path": "source.md"}],
  "slides": [
    {"id": "s1", "title": "判断句标题",
     "message": "这一页的唯一结论（可选但强烈建议）",
     "blocks": [
       {"role": "fact", "text": "原文中的事实", "source_ref": {"source_id": "doc", "loc": "para_2"}},
       {"role": "metric", "label": "总收入", "value": "+36%", "source_ref": {"source_id": "doc", "loc": "para_2"}},
       {"role": "list", "items": [{"text": "要点", "source_ref": {"source_id": "doc", "loc": "list_1"}}]},
       {"role": "table", "source_ref": {"source_id": "doc", "loc": "table_1"}},
       {"role": "insight", "text": "你的综合判断", "source_refs": [{"source_id": "doc", "loc": "para_3"}]}
     ]}
  ]
}
```

Block roles: `fact` / `quote` (verbatim-ish, `source_ref` **required**), `metric` (`label`+`value`, `source_ref` **required**, numbers must exist in the anchored element), `table` (references the source table — never retype cells), `image` (`asset_ref`: an `img_N` anchor), `list` (optional `semantics`: `steps|stages|options|criteria|findings`), and synthesized `insight` / `risk` / `recommendation` / `context` (optional `source_refs`).

Rules the engine enforces:

- **Select, don't invent.** Every fact/metric/quote/table is verified against the anchored source element. Fabricated numbers and dangling anchors are rejected with machine-readable errors.
- **Cover the source.** The engine checks section/table coverage. Don't read half the article and stop.
- **Content only.** No visual fields. The only presentation influence you have is `slides[].hints` (`emphasis_block_ids`, `tone`).
- Optional enrichment (better decks, never required): `message`, `relations` (`causal|comparison|sequence|hierarchy|dependency|contrast` between block ids), `slide_role`, `deck.narrative_intent`, `x_semantics`.

### Optional data visuals (v4.1 — stronger decks, never required)

A slide may carry one optional data payload; the engine renders it natively (chart or diagram). Weak models omit these and the engine infers an archetype from the blocks alone.

- `chart` — `{type: "column"|"bar"|"line"|"pie"|"combo", data: {categories: [...], series: [{name, values}]}, source_ref}`. Numbers must come from the anchored source; series colors and chart styling are engine-owned.
- `diagram_ir` — `{diagram_type: "causal_chain"|"phase_roadmap"|"layered_architecture"|..., nodes: [{label, priority}], edges: [{from, to, relation}], source_refs}`. Nodes/edges describe structure only — never positions, colors, or shapes.

Full example: `schemas/v4/examples/presentation-ir-v41-chart-diagram.json`.

### Step 4 — Compile

```bash
# with your IR (preferred):
python3 -m engine compile --source doc:markdown:source.md --ir ir.json \
  --no-degrade --output-dir out/

# without an IR (engine builds the deck from the source alone):
python3 -m engine compile --source doc:markdown:source.md --output-dir out/
```

Optional: `--style styles/<pack>.json` — available packs: `editorial-knowledge` (default), `consulting-light`, `technical-blueprint`, `product-report`, `consulting-blueprint-hybrid`. Ask the user which they want when it matters; validate custom packs with `python3 -m engine style-validate --style pack.json`.

Outputs in `out/`: `deck.pptx`, `render-plan.json`, `decision-trace.json`, `ir.json`, `compile-result.json`.

### Step 5 — Repair loop (max 3 rounds)

If compile with `--no-degrade` fails, `compile-result.json` contains `errors` with `stage`, `code`, `path` (slide-addressable), and the offending value:

- `LOC_NOT_FOUND` / `LOC_MALFORMED` — fix the anchor (re-check `parsed.json`).
- `QUOTE_MISMATCH` — your quote is not verbatim; copy the source text exactly or drop `quote`.
- `METRIC_VALUE_NOT_IN_SOURCE` — the number is not in the anchored element; fix the value or the anchor.
- Schema codes (`REQUIRED_FIELD_MISSING`, `ADDITIONAL_PROPERTY`, …) — fix the JSON shape; `ADDITIONAL_PROPERTY` usually means you wrote a visual field. Delete it.

Fix the IR, recompile. After 3 failed rounds, drop `--no-degrade` and recompile: the engine ships a verified extractive deck built from the source itself and records the fallback. Never hand-edit the output files; never bypass the engine to write PPTX yourself.

### Step 6 — Deliver honestly

Read `compile-result.json` and report to the user:

- the deck path and slide count;
- `ir_origin` (`provided` / `extractive` / `extractive_fallback` — the last means your IR was rejected; say so and why);
- `degradations` (truncations, font step-downs, image placeholders, KPI overflow) — every one is a bound the engine applied to guarantee delivery;
- coverage status, and which source sections were left uncovered.

Do not present a degraded or extractive deck as if it were fully IR-driven. The decision trace (`decision-trace.json`) explains every layout choice if the user asks why a slide looks the way it does.

## Quality expectations

- Slide titles should be judgments, not topics ("增长由海外驱动" not "收入情况"), carried in `title` + `message`.
- Group content so each slide makes one point; use `metric` blocks for numbers, `relations` for causality/comparison — they drive better archetypes.
- 3–8 blocks per slide is the sweet spot; the schema caps at 12.
- The engine guarantees the floor (no blank pages, no overflow, verified content). The ceiling — sharp selection, insight, narrative — is your contribution.

## Autonomy tiers (protocol extension slot)

This version runs every model at tier **L0**: zero visual authority, rules pick every archetype. Tiers **L1** (choose among engine-proposed archetype candidates) and **L2** (constrained composition proposals, QA-gated) are reserved protocol extensions; their activation and the behavioral probe that grants them will be documented here when enabled. Nothing in the current protocol changes when they arrive.

## Legacy v3 route

The v3 multi-contract pipeline (`scripts/run_pipeline.py`, `ppt-ir` v2 contracts) remains in-tree for compatibility and is superseded by this protocol. Do not mix the two routes in one delivery.

# PPT Smith v4 Contracts

v4 contracts define the boundary between any LLM and the PPT Smith engine. They are versioned with semver; breaking changes bump the major version and ship with a migration note.

## Design principles

1. **Content only.** The IR describes what each slide says — facts, metrics, lists, tables, relations, insights — never how it looks. Layout, archetype, typography, color, and density are engine-owned. Schemas enforce this with `additionalProperties: false`: visual fields are rejected, not ignored.
2. **Minimal viable protocol.** The required core is tiny: `deck.title` + `slides[].{id, title, blocks(>=1)}`. Any model that can produce this gets a complete, professionally laid-out deck. Everything else (`message`, `relations`, `slide_role`, `hints`, `x_semantics`) is progressive enrichment.
3. **Source anchoring.** `fact` / `quote` / `metric` / `table` blocks must carry a `source_ref` pointing at a structural anchor (`para_12`, `table_1`, …) emitted by the deterministic source parser. The engine verifies anchored content against the source and rejects fabrication. Model-synthesized blocks (`insight`, `risk`, `recommendation`, `context`) take optional `source_refs`; unanchored synthesis renders with lower visual authority.
4. **Bounded influence.** The only model-supplied presentation influence is `slides[].hints` — declared, enumerated knobs (emphasis ranking, tone). Everything visual beyond that is decided by the engine's Design Policy and recorded in the decision trace.
5. **Open extension.** `x_semantics` objects at deck and slide level accept richer semantics from stronger models. The engine uses keys it understands and ignores the rest — enrichment never breaks weaker producers.

## Files

| File | Status | Purpose |
|---|---|---|
| `presentation-ir.schema.json` | frozen 4.0.0 | LLM → engine content contract |
| `examples/presentation-ir-minimal.json` | reference | The weak-model floor: titles + anchored facts/lists |
| `examples/presentation-ir-enriched.json` | reference | Full enrichment: metrics, relations, insights, hints |
| `style-contract-v4.schema.json` | frozen 4.0.0 | User-authorable visual-system data pack: L1 tokens (free within hard floors), L2 skins (token references only — raw colors rejected), bounded `layout_knobs`, `pack` distribution metadata for open and commercial packs |
| `examples/style-editorial-v4.json` | reference | The v3 `editorial-knowledge` style migrated to pack format |
| `decision-trace.schema.json` | frozen 4.0.0 | Engine decision log: dual evidence (structural + semantic) as content-free features, candidates with confidence, chosen-by attribution (rule / advisor / proposal / override / fallback), degradation outcomes |
| `examples/decision-trace-example.json` | reference | A three-decision trace with L1 advisor pick and rule decisions |
| `render-plan.schema.json` | frozen 4.0.0 | Engine → builder geometry contract: integer EMU + centipoints, resolved colors, native connector rules; builders execute, never design |
| `examples/render-plan-example.json` | reference | One slide: title, two KPI cards, bound causal connector |

Validation: `scripts/validate_contracts.py --strict --presentation-ir <f> --style-v4 <f> --decision-trace <f> --render-plan <f>` (stdlib-only), cross-checked against `jsonschema` Draft 2020-12 in the test suite.

## Differences from v3 `ppt-ir.schema.json`

| v3 | v4 |
|---|---|
| Model authors `primary_expression`, `page_archetype`, `layout_intent`, `primary_anchor`, `density`, `delivery_contract`, `qa_expectations` per slide | Removed from the model contract entirely; engine decides, decision trace records |
| `source_refs` exist but content is free-form | Anchors are grammar-checked (`<element>_<index>[#span]`) and deterministically verified, with optional verbatim `quote` |
| Judgment fields required (`audience_question`, `title_role`, `judgment`) | Optional single `message`; judgment quality is model-dependent enrichment, not a validity requirement |
| Tables retyped by the model into objects | `table` block references the source table; the engine extracts cells from the parsed source |
| One flat contract for strong models | Minimal core + progressive enrichment; validity is reachable by weak models |

v3 contracts remain in `schemas/` and stay authoritative for the v3 pipeline until the v4 engine path replaces it.

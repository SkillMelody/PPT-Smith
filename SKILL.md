---
name: "article-html-to-ppt"
description: "Author professional, editable PPTX decks from Markdown, HTML, text, PDF, data, or a user template. A capable model owns source understanding, narrative, slide content, visual encoding, component selection/composition, speaker notes, and any new native components; PPT Smith supplies source anchors, reviewed template components, deterministic execution, real rendering, and fail-closed QA. Use for bespoke decks, template-driven decks, and diagnostic standard compilations."
metadata:
  display_name: "MeowClaw PPT Smith"
  english_alias: "MeowClaw PPT Smith"
  public_slug: "meowclaw-pptsmith"
  version: "4.1.0-beta.1"
  compatibility_aliases: ["article-html-to-ppt", "meowclaw-decksmith"]
---

# MeowClaw PPT Smith v4 — Model-Directed Presentation Authoring

PPT Smith is a model-directed authoring system, not a model-independent content
generator. A capable model must understand the source, decide what the deck
says, choose how each idea is expressed, and inspect the rendered result. The
engine verifies and executes those decisions; it does not replace them with a
generic extractive deck.

## Non-negotiable authoring contract

For a final delivery, the model owns:

- complete source reading and evidence selection;
- audience, purpose, narrative arc, section order, and page budget;
- assertion-led slide titles and concise visible copy;
- chart data, comparisons, sequences, hierarchies, and other relationships;
- template-component matching and multi-component composition;
- new native components when the reviewed template cannot express the idea;
- speaker notes containing detailed explanation, evidence, caveats, and source
  anchors;
- visual review of the real rendered candidate.

PPT Smith owns deterministic source anchors and provenance checks, reviewed
template-component contracts, native-object execution, rendering, structural
inspection, and fail-closed delivery states.

If the active model cannot complete the authoring contract, stop with
`MODEL_AUTHORING_REQUIRED`. Do not disguise an extractive or placeholder deck
as a final presentation.

## Choose one route

### Bespoke — default for the quality ceiling

Use when the user wants the strongest result and strict template reuse is not
required. The model authors the narrative, geometry, native charts, diagrams,
and visual system from a blank presentation. A reference deck may guide style,
but is not claimed as a preserved template.

Read [docs/v4-bespoke-architecture-plan.md](docs/v4-bespoke-architecture-plan.md).

### Template — model-directed component reuse

Use when the user supplies a PPTX template or asks to preserve its native
visual language. The model must analyze both source and template, then:

1. build or load a reviewed Component Atlas;
2. decompose each planned slide into semantic slots;
3. reuse every feasible template component before inventing a replacement;
4. compose multiple template components when one component is insufficient;
5. create a new native component in the template's visual language when no
   reviewed component fits;
6. bind every new component to one or more reviewed template components as its
   visual-grammar reference;
7. record why every feasible component was selected or rejected.

A reviewed component is a module, not automatically a complete slide. Every
Template body page also needs a `page_composition` contract with a page recipe
and real variant, a template-neutral `composition_archetype`,
assertion/evidence/interpretation/implication layers, at
least two substantive content modules, an information-unit count, and a
takeaway. Quantitative pages additionally require visible key numbers and
chart annotations. Reject title-plus-single-component shells even when the
component itself is perfectly cloned.

An illustration from the source may be used only when it is an isolated
illustration or non-reconstructable figure. Never use a screenshot containing
source-page prose, navigation, headers, or footers as a slide substitute.

Detect cover and closing support only from reviewed full-page recipes. A widget
whose name merely contains `cover` or `closing` is not a boundary-page recipe.
When the uploaded template has no qualifying cover or closing page, author an
original one from the template's typography, palette, spacing, line, and icon
grammar and declare `style_derived_original`; do not force an unrelated template
component into that role.

Read [docs/v4-template-route.md](docs/v4-template-route.md).

### Standard / Engineering — diagnostic only

Use for deterministic smoke tests, schema checks, layout diagnostics, or an
explicitly requested engineering draft. Standard output is not a final-quality
substitute for model-authored Bespoke or Template work.

Read [docs/v4-three-route-architecture.md](docs/v4-three-route-architecture.md).

## Required model workflow

### 1. Establish the production request

Confirm or infer the audience, decision, language, route, page-range contract,
template-use mode, delivery format, and editability requirements. A source-page
count is not an output-slide count.

### 2. Read and structure the entire source

Stage source files locally, then obtain deterministic anchors:

```bash
python3 -m engine parse --source report:text:source.txt --json-out parsed.json
```

For PDF, preserve page identity and extract tables, charts, illustrations, and
captions as distinct source objects where possible. Reconcile the deterministic
parse with the actual source pages; do not rely on an early subset.

### 3. Author the content contracts

Before choosing geometry, produce:

- Content & Evidence Map;
- Narrative Contract and page budget;
- source-backed Presentation IR;
- per-slide assertion, evidence, topology, visible-content, and speaker-notes
  contracts;
- chart/table/diagram payloads for every reconstructable quantitative exhibit;
- Exhibit Interpretation Contract for every retained illustration.

Visible copy should contain one assertion and a small number of complete,
high-value labels. Detailed reasoning belongs in speaker notes. Planner-created
ellipsis, OCR fragments, generic labels, and tiny source prose are forbidden.

Final visible copy must also reject unresolved generator values such as
`undefined`, `null`, `NaN`, `[object Object]`, TODO/TBD, and Chinese placeholder
equivalents. Duplicate or overlapping slide-number objects are delivery
failures, not harmless decoration.

The IR schema is [schemas/v4/presentation-ir.schema.json](schemas/v4/presentation-ir.schema.json).

### 4. Analyze the template when using Template route

```bash
python3 -m engine component-atlas \
  --template-pptx template.pptx \
  --review component-review.json \
  --json-out component-atlas.json
```

The review must identify reusable charts, tables, timelines, processes, KPI
cards, comparisons, matrices, image frames, relationship diagrams, section
recipes, style primitives, and equivalent instances. It must also state whether
each component can stand alone, its minimum information units, recommended
page recipes and companions, annotation requirements, and prohibited uses.
Geometry alone is not a semantic component review.

For every uploaded template, derive a template-local adaptation contract:
content and decoration bounds, background semantics, supported aspect ratios,
responsive modes, minimum visible information, numeric annotation floors, and
series role. Do not encode component ids, page numbers, colours, fonts, or
sample-report rules from a previously tested template. Oversized source-page
backgrounds are not reusable component content unless the reviewed contract
proves a semantic role.

### 5. Let the model compose the deck

For every slide, compare its topology, data shape, required slots, text bounds,
and element capacity with the Atlas. Record:

- feasible template components;
- selected component(s) and slot bindings;
- rejected candidates and reasons;
- any model-authored native component required;
- speaker notes and evidence IDs.

The model may specify composition and geometry for Bespoke pages and for new
Template components. Existing reviewed Template components retain their native
geometry unless an explicitly supported placement transform is used.

External visual assets used by a Template component require a declared source,
license or permission basis, and content hash. Do not copy icons or graphics
from style references merely because they resemble the uploaded template.

### 6. Execute and verify

Useful route commands include:

```bash
python3 -m engine plan-bespoke ...
python3 -m engine author-bespoke ...
python3 -m engine plan-model-template-components ...
python3 -m engine component-atlas-report ...
python3 -m engine compose-components ...
python3 -m engine strict-template ... --final-delivery
python3 -m engine review-template ...
```

`plan-manuscript-components` remains available for legacy diagnostics. It is
not a substitute for a model-authored slide plan. A `model_authored` Template
component is executed through `build(slide, context)` and may use only native
objects plus explicitly hash-bound standalone source illustrations declared in
the IR.

Always run structural inspection and a real renderer. A generated PPTX is only
a candidate until visual review is bound to that candidate.

### 7. Review the rendered deck

Inspect every slide, not only a contact-sheet thumbnail. Reject for:

- weak or incomplete content expression;
- source-page screenshots used as authored slides;
- reconstructable data shown only as raster images;
- visible truncation or planner-created ellipsis;
- sparse text/outline pages without purposeful composition;
- feasible template components left unused without explanation;
- inconsistent template style, hierarchy, spacing, density, or rhythm;
- a reviewed component used as the whole page without supporting evidence,
  interpretation, or implication;
- repeated declared variants that do not correspond to genuinely different
  compositions;
- repeated real-rendered visual skeletons even when their recipe names or
  left/right orientation differ;
- components mechanically scaled into unsupported target aspect ratios;
- comparison series without a shared anchor and scale, or long series that
  should be consolidated or moved to an appendix;
- missing or inadequate speaker notes.
- rendered semantic modules that do not account for the model's declared
  information units;
- body text below the Template readability floor;
- unresolved generator values or duplicate slide-number objects.

## Final-delivery gates

A final deck requires all applicable gates:

- source and numeric provenance pass;
- important-evidence coverage pass;
- every body slide has a complete assertion;
- every body slide has speaker notes with evidence and source anchors;
- every reconstructable chart/table is native and editable;
- every feasible reviewed template component is reused or has a documented
  rejection reason;
- no page screenshot contains source prose/navigation/header/footer;
- no generic placeholder or planner-generated ellipsis is visible;
- component binding, structural inspection, real rendering, asset integrity,
  deck rhythm, content density, and style completeness pass;
- hash-bound human or capable-model visual review approves the candidate.

If any gate fails, return a candidate/revision state and the exact blocker. Do
not call it final.

## Route isolation and references

Do not mix route authority: Standard rules cannot override Bespoke design;
Bespoke cannot claim strict template preservation; Template cannot use
unreviewed or semantically mismatched components merely to increase reuse.
Template-only page-composition and component-suitability gates must not be
imported into Bespoke or Standard runtimes.

- [V4 route architecture](docs/v4-three-route-architecture.md)
- [Bespoke route](docs/v4-bespoke-architecture-plan.md)
- [Template route](docs/v4-template-route.md)
- [Template generalization contract](docs/v4-template-generalization.md)
- [Legacy Standard style-pack guide](docs/template-authoring-guide.md)
- [Template whole-page design plan](docs/v4-template-whole-page-design-plan.md)
- [Presentation IR examples](schemas/v4/examples/)

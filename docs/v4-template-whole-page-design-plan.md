# V4 Template Whole-Page Design Plan

## Goal

Raise Template-route output from component placement to professional whole-page
authoring while preserving source provenance, native editability, reviewed
template reuse, speaker notes, and fail-closed delivery.

The reference MGI Chinese deck is evidence for useful page-composition patterns,
not an asset library or a new fixed template. No external icon, color, font,
geometry, or page-specific rule may be copied into the engine.

## Scope and route isolation

This plan applies only to `route=template` and its strict runtime. Bespoke keeps
its independent quality-ceiling workflow; Standard remains diagnostic. New
Template modules must not be imported by either route.

## Phase 1 — Whole-page composition contract

Extend each body-page contract to express:

- assertion and audience decision;
- primary visual/evidence module;
- key numbers and annotations;
- interpretation and implication modules;
- optional contextual navigation;
- takeaway and speaker notes;
- composition archetype and real rendered variant.

Maintain a template-neutral recipe taxonomy for executive summaries, data
comparisons, mechanisms, case studies, country/portfolio dashboards,
methodology pages, action frameworks, and boundary pages. Recipes define
semantic roles and hierarchy, not fixed coordinates.

Acceptance:

- every body page has at least two substantive modules and four information
  units;
- quantitative pages expose values, units, comparison basis, and annotation;
- one reviewed widget cannot masquerade as a completed slide;
- cover and closing pages use reviewed full-page recipes or declared
  `style_derived_original` designs.

## Phase 2 — Semantic saturation and visual granularity

Measure the rendered expression of the page, not only visible character count:

- bound semantic-object count;
- meaningful text modules;
- quantitative annotations;
- charts, tables, diagrams, and semantic icons;
- declared versus rendered information units;
- whitespace and real layout fingerprint.

Do not impose a universal object-count target: different templates use
different levels of grouping. Fail only when the rendered page cannot account
for the semantic modules declared by the model.

Acceptance:

- declared information units have visible bound representations;
- long prose cannot substitute for primary evidence plus interpretation;
- decorative objects do not count as semantic saturation;
- repeated left/right mirrors remain one visual skeleton.

## Phase 3 — Template-native composition and style-derived components

Keep two explicit modes:

1. `strict`: preserve the uploaded template's theme, masters, layouts, and
   reviewed native components; every feasible component is reused or rejected
   with a page-fit reason.
2. `style_derived_original`: used only where the reviewed Atlas lacks a
   feasible component; the model must cite visual-reference components and use
   the template's extracted design grammar.

New components must inherit typography, semantic color roles, spacing, line,
corner, icon, and density grammar from the active template. Any external visual
asset requires a declared source, license/permission basis, and content hash.

Acceptance:

- strict output retains the template package parts required by the route;
- style-derived output cannot be reported as native component reuse;
- no brand-, page-, color-, or component-ID special case exists in production
  logic.

## Phase 4 — Page-recipe execution

Add reusable Template authoring recipes for:

- four-finding executive summary;
- narrative sequence and mechanism;
- chart plus annotated evidence and takeaway;
- sector/value mix;
- skill composition and demand signal;
- case comparison with deployment/problem/result/role-shift fields;
- country comparison and selective deep dive;
- action framework by stakeholder.

Each recipe selects and composes reviewed template components first. It may
request a style-derived native component only after component-fit evaluation.

## Phase 5 — Final-delivery QA

Add actual-PPTX checks for:

- visible `undefined`, `null`, `NaN`, `[object Object]`, TODO/TBD, lorem ipsum,
  and equivalent Chinese placeholders;
- duplicated/overlapping footer page numbers;
- body text below 12 pt, excluding declared source/caption/page-number roles;
- declared semantic modules missing from the rendered page;
- missing speaker notes or evidence anchors;
- generic deck-level citations used instead of slide/object provenance;
- undeclared external icons or images;
- inconsistent exact/rounded metrics without a derivation note.

These checks run only in strict Template final-delivery mode and return precise
slide IDs and object names.

## Phase 6 — Validation matrix

Validate on bright consulting, dark technology, minimalist 4:3 business,
chart-heavy, image-led, Chinese government/enterprise, and an unseen holdout
template. For every template, test Atlas completeness, background semantics,
responsive fit, whole-page saturation, strict/style-derived disclosure,
rendered rhythm, and route isolation.

## Phase 7 — MGI acceptance

Re-author MGI from source-backed IR using the new contracts. The useful lessons
from the external deck are page hierarchy, micro-information units, annotated
evidence, case structure, and country comparison—not its assets or fixed
palette.

Final acceptance requires no placeholders or duplicate page numbers, body text
at least 12 pt, complete notes and object-level provenance, native
reconstructable charts, per-page template reuse disclosure, rendered rhythm,
hash-bound all-slide visual review, and full repository regression.


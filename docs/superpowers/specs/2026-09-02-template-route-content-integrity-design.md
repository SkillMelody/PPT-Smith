# Template Route Content Integrity Design

## Goal

Turn the V4 Template route from a geometry-preserving component transplant pipeline into a fail-closed, source-complete presentation pipeline. The route must preserve template-native editability while proving that important source claims, numbers, exhibits, and relationships survive planning, component selection, rendering, and delivery.

## Problem Statement

The 2026-09-02 real 30-page acceptance run established that component mechanics are not the limiting factor:

- 40 component operations executed and 85/85 semantic elements rendered.
- All 30 output slides rendered in LibreOffice.
- Only 14 of 293 source anchors were referenced, a 4.78% source-anchor coverage rate.
- 27 of 30 slides contained fewer than 80 visible characters.
- `card_grid` and `icon_card_grid` accounted for 17 of 30 slides.
- Generated labels such as `要点`, `顺序`, and `核心议题` made incomplete content look structurally valid.

The current pipeline validates that declared IR content was bound. It does not validate that the IR contains the important source content. Layout-pattern routing also maps unrelated information structures to the same component family. The result is a technically valid but semantically incomplete deck.

## Design Principles

1. **Source before slides.** Every slide claim and datum must originate in a source evidence unit.
2. **Content before geometry.** Component selection starts only after a slide content contract is complete.
3. **Topology before family.** Comparison, sequence, causality, hierarchy, risk, and metric structures are not interchangeable.
4. **Fail closed.** Missing required evidence, generic fallback copy, or a component that cannot bind required slots rejects the candidate.
5. **Coverage and factuality are separate.** A factually correct deck may still omit most of the report; both must pass.
6. **Route isolation remains intact.** Template-specific policy must not weaken Standard or Bespoke behavior.
7. **Real rendering remains mandatory.** Structural correctness is necessary but not sufficient for delivery.

## Scope Decomposition

The design is implemented as three independently testable subprojects. Each subproject receives its own implementation plan and may not silently absorb work from a later phase.

### Subproject A — Content Integrity Foundation

This is the first implementation cycle.

- Introduce source evidence units and a deck evidence ledger.
- Introduce per-slide content contracts.
- Extend coverage from advisory section/table counts to weighted evidence, required evidence, numeric, and exhibit coverage.
- Add a Template fail-closed content-integrity gate before component planning.
- Reject generic generated labels in final candidates.
- Preserve explicit source references through manuscript composition and strict-preview IR.
- Correct the asset-preservation check to compare only assets reachable from delivered slides.
- Make the real Template integration fixture reproducible from the registered worktree.

### Subproject B — Topology-First Component Planning

- Classify evidence topology before component selection.
- Add reviewed component slot contracts and capacity limits.
- Replace direct `layout_pattern -> family` routing with candidate filtering and scoring.
- Add reuse penalties and deck-level family diversity constraints.
- Require dedicated contracts for cover, section, data, method, and closing pages.

### Subproject C — Evaluation and Visual Quality Floor

- Add archetype-specific density and readability gates.
- Promote overflow, low contrast, unlabeled relations, and blank semantic shapes to blockers.
- Add factual-consistency evaluation using deterministic source checks first and optional QA/NLI adapters second.
- Add a reproducible baseline/ablation/full-system experiment harness.
- Re-run the fixed 30-page McKinsey case and at least two additional document/template pairs.

## Core Data Contracts

### Evidence Unit

An evidence unit is the smallest source-backed fact that may be selected or omitted deliberately.

```python
EvidenceUnit = {
    "evidence_id": str,
    "source_ref": {"source_id": str, "loc": str, "quote": str | None},
    "kind": "claim" | "metric" | "comparison" | "trend" | "process" | "method" | "risk" | "exhibit",
    "text": str,
    "entities": list[str],
    "numbers": list[{"value": str, "unit": str | None, "period": str | None}],
    "relations": list[{"type": str, "source": str, "target": str}],
    "salience": float,
    "must_keep": bool,
    "exhibit_id": str | None,
}
```

Evidence IDs are stable for the same parsed source. The extractor must not invent facts; it may only normalize source text and relationships that can be traced to an anchor.

### Deck Evidence Ledger

```python
EvidenceLedger = {
    "schema_version": "1.0.0",
    "sources": list[{"source_id": str, "sha256": str}],
    "evidence_units": list[EvidenceUnit],
}
```

The ledger is generated before the storyboard. All later coverage reports compare selected evidence IDs with this ledger.

### Slide Content Contract

```python
SlideContentContract = {
    "slide_id": str,
    "assertion": str,
    "evidence_ids": list[str],
    "required_evidence_ids": list[str],
    "topology": "statement" | "comparison" | "trend" | "sequence" | "causal" | "hierarchy" | "matrix" | "risk_mitigation" | "dashboard" | "method",
    "required_slots": list[str],
    "source_footer_required": bool,
    "omissions": list[{"evidence_id": str, "reason": str}],
}
```

Every body slide requires a sentence-level assertion and at least one evidence unit. Cover, section, and closing slides use explicit archetype exceptions; they do not receive generic body-slide exemptions.

## Pipeline

```text
parsed sources
  -> evidence extraction
  -> evidence ledger validation
  -> slide allocation and content contracts
  -> content-integrity gate
  -> topology-first component planning
  -> strict native binding and cloning
  -> semantic delivery gate
  -> reachable-asset preservation
  -> structural QA and real rendering
  -> visual acceptance report
```

### Hierarchical Source Processing

Long documents are processed per section or source page, then reconciled globally:

1. Extract evidence locally so middle sections are not lost in a single long-context pass.
2. Assign salience and `must_keep` status using deterministic rules for headings, exhibits, tables, repeated conclusions, and numeric findings.
3. Build a global outline that allocates evidence to slides without duplication.
4. Reconcile unallocated `must_keep` evidence before any component is selected.

## Content-Integrity Gate

The existing `coverage_report()` remains a low-level report generator. A new Template policy layer interprets it together with the evidence ledger and slide contracts.

The initial acceptance policy is:

- Required evidence coverage: 100%.
- Weighted evidence coverage: at least 90%.
- Numeric evidence recall: at least 95%.
- Exhibits: 100% represented or accompanied by a non-empty omission reason.
- Every body slide: a non-empty assertion and at least one source-backed evidence unit.
- Every declared source reference: valid under the existing provenance verifier.
- Generic fallback labels: zero occurrences in a delivery candidate.

Thresholds are route-scoped configuration with these values as Template defaults. Unit tests may use explicit lower thresholds to exercise boundary behavior.

The gate returns stable issue codes, including:

- `REQUIRED_EVIDENCE_MISSING`
- `WEIGHTED_COVERAGE_BELOW_FLOOR`
- `NUMERIC_EVIDENCE_MISSING`
- `EXHIBIT_OMISSION_UNEXPLAINED`
- `SLIDE_ASSERTION_MISSING`
- `SLIDE_EVIDENCE_MISSING`
- `GENERIC_DELIVERY_LABEL`
- `SOURCE_REFERENCE_INVALID`

## Generic Copy Policy

The planner may not synthesize `要点 N`, `顺序`, `核心议题`, unnamed stages, or numeric badges solely from item position for a final candidate. Required component labels must be supplied by the slide content contract. If a reviewed component requires a label that the contract cannot supply, that component is infeasible.

Diagnostic placeholders such as `组件待补充` remain permitted only in explicitly marked non-delivery preview artifacts. They make delivery status fail and cannot be included in a candidate marked verified.

## Topology-First Component Selection

Subproject B introduces a two-stage selector:

1. **Feasibility filter:** topology support, required slots, element capacity, chart/table capability, and text bounds must all match.
2. **Deck-aware ranking:** semantic fit, evidence-slot coverage, capacity fit, native fidelity, text-fit risk, reuse penalty, and adjacent-family penalty determine the winner.

An illustrative ranking function is:

```text
score = 0.30 topology_fit
      + 0.25 required_slot_coverage
      + 0.15 capacity_fit
      + 0.10 evidence_type_fit
      + 0.10 native_fidelity
      + 0.10 deck_diversity
      - overflow_risk
      - generic_fallback_penalty
```

Hard feasibility failures cannot be overcome by a high score. The exact weights live in a route-scoped policy object and are covered by ordering tests.

Deck-level diversity defaults:

- No component family appears on more than two consecutive slides.
- No generic card family occupies more than 35% of body slides.
- Data, method, cover, section, and closing archetypes must use components reviewed for those archetypes.

## Strict Preview and Source Propagation

`build_manuscript_strict_preview_bundle()` must include source references on the IR blocks and items it creates. The strict-preview summary must report evidence counts and coverage, not only operation counts. A component operation is considered supported only when all required contract slots and evidence references are bound.

## Reachable Asset Preservation

The current check compares every master, layout, theme, and media path in the source template with the output subset. That incorrectly fails when an unused template slide and its private media are omitted.

The replacement computes the relationship graph reachable from delivered slides, their layouts, masters, themes, charts, embedded workbooks, and media. Every reachable source part must exist in the output with identical bytes or an explicitly tracked content-hash-preserving remap. Unreachable template assets are outside the delivery contract.

## Error Handling

- Invalid ledgers or slide contracts fail before component planning.
- Missing `must_keep` evidence never triggers an extractive degradation that hides the failure.
- An infeasible component produces a structured planning gap, not a generic fallback component.
- Visual or structural blockers reject delivery but retain diagnostic artifacts.
- Optional QA/NLI services may return `inconclusive`; they may not override deterministic coverage or provenance failures.

## Testing Strategy

### Unit Tests

- Stable evidence-unit extraction and IDs.
- Weighted, required, numeric, and exhibit coverage boundaries.
- Content-contract validation and issue codes.
- Generic copy rejection.
- Source-reference propagation into strict-preview IR.
- Topology feasibility and ranking order.
- Diversity constraints across a deck.
- Reachable versus unreachable asset preservation.

### Integration Tests

- A minimal real template fixture stored or generated inside the registered worktree.
- A manuscript with deliberately omitted middle-section evidence must fail.
- A complete manuscript must pass content integrity before strict rendering.
- A slide-subset output may omit unreachable media and still pass asset preservation.
- A reachable modified asset must fail.

### Real Acceptance Experiment

Use the same source PDF and template hashes from the 2026-09-02 acceptance run.

- **A — Baseline:** current planner and QA.
- **B — Content integrity:** evidence ledger, slide contracts, and fail-closed coverage.
- **C — Full system:** B plus topology-first selection, diversity, and enhanced visual QA.

Report source evidence recall, required evidence recall, numeric recall, exhibit handling, factual errors, generic labels, overflow/collision findings, family concentration, and blinded human ratings for completeness, clarity, visual quality, trust, and delivery readiness.

## Acceptance Criteria

Subproject A is complete only when:

- New tests demonstrate red-green behavior for every added policy.
- The Template-focused suite passes from the registered worktree.
- The real integration fixture runs without an external untracked project directory.
- The fixed 30-page baseline is rejected for content incompleteness with stable issue codes.
- A complete fixture passes the new content gate.
- Generic fallback labels reject delivery.
- Unreachable omitted media no longer causes asset-preservation failure, while modified reachable media does.

The entire design is complete only when Subprojects A, B, and C pass their own plans and the full-system arm C reaches:

- 100% required evidence coverage.
- At least 90% weighted evidence coverage.
- At least 95% numeric recall.
- 100% exhibit representation or documented omission.
- Zero generic delivery labels.
- Zero error-level structural or visual findings.
- At least 90% of slides passing blinded human delivery-readiness review.

## Non-Goals

- Changing Standard or Bespoke layout authority.
- Making every shape in a template a reviewed component.
- Using a vision model as the sole delivery gate.
- Maximizing text density without regard to archetype or readability.
- Publishing, pushing, or merging the branch as part of implementation.


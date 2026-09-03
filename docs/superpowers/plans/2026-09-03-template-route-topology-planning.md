# Template Route Topology-First Component Planning

## Goal

Replace the Template route's direct `layout_pattern -> component family` decision with a fail-closed sequence: classify source-backed information topology, filter reviewed components by topology and required slots, then apply deck-level diversity rules.

## Scope and order

1. **Topology contract and migration classifier** — add a bounded topology vocabulary; content bindings are authoritative, legacy layout patterns are migration-only; unknown topology becomes a planning gap. *(Started: `engine/topology.py` with unit tests.)*
2. **Reviewed component capability metadata** — record each component's supported topologies, required semantic slots, and capacity in the atlas; old components without reviewed metadata are ineligible for delivery candidates.
3. **Feasibility-first planner** — choose components only after topology, required slot, text/capacity, and chart/table capability checks; return stable planning-gap codes instead of fallback cards.
4. **Deck-aware selection** — score feasible candidates using evidence-slot coverage, capacity fit, native fidelity, reuse penalty, and adjacent-family penalty. Enforce no more than two consecutive identical families and ≤35% generic-card body pages.
5. **Integration acceptance** — the deficient 30-page case must fail for planning gaps rather than route all pages to cards; a complete fixture must produce diverse reviewed choices with source-backed slots.

## Verification

- Unit tests cover explicit-over-legacy precedence, legacy migration mapping, and unclassified failure.
- Existing Template content-integrity suite remains green.
- No Standard or Bespoke code path may consume Template topology policy.
- The final Subproject B report records selected topology, candidate set, rejection reasons, and family distribution per slide.

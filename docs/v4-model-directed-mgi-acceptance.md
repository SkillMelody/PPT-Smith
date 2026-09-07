# V4 Model-Directed Template Authoring — MGI Acceptance

## Scope

This phase replaces the model-agnostic positioning with the V3-inherited,
model-led quality route and adds Template-specific component analysis,
composition, new native component authoring, speaker notes, and final visual
review gates.

## MGI 40-page result

- final state: `final_delivery_ready`;
- 40 rendered slides and 40 non-empty speaker-note pages;
- 19 native editable charts;
- 20 slides with explicit reviewed-template component composition;
- 20 slides with task-specific model-authored native components;
- 0 source-page screenshots and 0 picture objects;
- 0 visible ellipses;
- 0 newly introduced structural findings;
- content integrity, component intent, binding, template assets, readability,
  real rendering, density, and hash-bound visual review passed.

The post-review revision removes the non-template robot-to-person graphic,
replaces sparse/repeated pages with reviewed progression, cycle, icon-card,
management-dimension, and evidence-list components, and emits a 24-row
Component Atlas suitability table for human review.

Artifacts are in the ignored acceptance run directory:

`test-runs/mgi-model-directed-20260907/`

Primary delivery:

`mgi-model-directed-template-final.pptx`

## Regression

Full repository regression after the final fixes:

```text
697 passed, 16 skipped in 1980.36s
```

The skipped cases are the repository's existing environment/fixture skips; no
test failed.

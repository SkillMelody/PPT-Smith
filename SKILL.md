---
name: "article-html-to-ppt"
description: "Create editable PPTX from documents, reconstruct supplied slide design images, or preserve native PPTX templates. Design with structured native objects and real previews; image-generation tools are optional. Use for source-based presentations, design-to-PPT reconstruction, template reuse, and revisions to PPT Smith tasks."
metadata:
  display_name: "MeowClaw PPT Smith"
  english_alias: "MeowClaw PPT Smith"
  public_slug: "meowclaw-pptsmith"
  version: "5.1.1"
  compatibility_aliases: ["article-html-to-ppt", "meowclaw-decksmith"]
---

# MeowClaw PPT Smith

## Select the user's intent

| User wants | Route | Read when selected |
| --- | --- | --- |
| Make a presentation from a document, optionally with brand/style references | `create` (default) | [Declarative workflow](references/declarative-design.md) |
| Reconstruct supplied complete slide designs as editable objects | `recreate` | [Declarative workflow](references/declarative-design.md) |
| Reuse a native PPTX template and its components | `template` | [Template workflow](references/routes/v4-template-route.md) |

Infer intent, audience, language and page budget from the request. Ask only about material conflicts, such as exact image reconstruction versus native template preservation. A style image does not imply exact reconstruction. A PPTX supplied only as a style reference uses create; preserve masters/native layouts only when requested. For template-inspired redesign, read [template visual design](references/template-visual-design.md). A source page count does not prescribe slide count.

## Shared authoring contract

Read the full source once, preserve page/evidence anchors, then use the relevant evidence for each slide. The model owns narrative, assertion titles, visual encoding and page-specific design. The backend executes those decisions; it does not replace them with generic extractive layouts. Insufficient authoring capability returns `MODEL_AUTHORING_REQUIRED`.

Choose typography, palette, composition and visual rhythm for the current content, audience and references. Do not copy the last task's colours, card layout, footer or brand. Reusable components are primitives, not mandatory page styles.

Keep checked text/data in content records, geometry in scene records, and detailed reasoning, sources and qualifications in speaker notes. Unknown chart data stays unknown. Reconstructable charts/tables use native data; isolated pictures are replaceable assets, not editable internal objects. Do not insert a whole-page screenshot to claim editable reconstruction. Disclose deliberate simplifications and accepted raster exceptions.

## Efficient native design and revisions

For create/recreate run `python3 -m engine design capabilities`. The host supplies model capabilities; local code cannot infer whether the current model sees or generates images.

For **create**, author structured design, render a native candidate to PNG, inspect and revise it. Image generation is optional for independent illustrations or an explicitly requested external design target. No image tool is needed for ordinary native design. Do not convert your own preview into a fake external reference or claim self-comparison proves design quality.

For **recreate**, visually read the supplied complete target, verify its content against the source, and preserve approved geometry. Do not invent source numbers from chart pixel heights. Keep original targets, approved changes and actual PPTX previews distinct.

Use the compact author format and page-scoped context described in the selected guide. The fixed compiler expands style/source/symbol references into validated native objects. Do not execute task-authored scripts to bypass unsupported features.

Run the real-office font preflight before expanding a large deck. Check representative compositions first; continue without mandatory user approval unless the request needs a consequential choice. Fontconfig matching alone does not prove actual Chinese font rendering.

Default tool feedback is a summary. Read full reports only for relevant failures; keep task state and evidence in files. Use guarded object patches instead of rewriting the deck. For changed builds, inherit independent page review only through the verified inheritance command; changed content, notes, geometry, assets, fonts or renderer invalidate the affected evidence.

## Review and delivery

Actual PPTX rendering, checked content/data, resolved fonts, structural editability, target-software edit/save/reopen checks, and independent visual review are required. Review every new or changed page at readable resolution; a contact sheet alone cannot verify small text.

Original design without an external target uses `reconstruction: not_applicable`; design, content, fonts and editability still require approval. Reconstruction with a target requires fidelity approval. Reused review must retain its original reviewer observations and evidence, never a fabricated second identity. A generator's own review is not independent.

`candidate_unreviewed`, `draft`, and `render_incomplete` are not final. Deliver only when the exact candidate passes the selected route's gates. User-visible output includes editable PPTX, actual preview and material editing limitations.

Quality acceptance is separate from OS isolation. `--isolation auto` chooses available macOS isolation or host execution. Host may deliver after quality acceptance, while reporting OS isolation unverified. `--require-os-isolation` remains binding; do not downgrade it. Do not claim untested PowerPoint/WPS or cross-platform parity.

## Compatibility only

Legacy `new_design` and `style_transfer` init arguments map to create; register requested style references explicitly. Existing saved legacy tasks retain their old target contract. Draft is a state/diagnostic option, not another production promise.

Bespoke remains an advanced compatibility authoring route where needed: read [its guide](references/routes/v4-bespoke-route.md). Template preserves native assets and never silently falls back to blank-slide reconstruction. Their detailed [V4 authoring contract](references/routes/v4-authoring-contract.md) loads only for those routes.

Standard / Engineering remains available for internal diagnostics and explicit engineering drafts, not as a substitute for final model-authored design. Do not load all compatibility guides for a normal create task.

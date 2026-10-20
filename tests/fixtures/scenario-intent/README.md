# Scenario-intent iteration record

Date: 2026-10-19. Version remains 5.2.1; this is an unreleased guidance change.
All prompts in this directory are synthetic, written for internal validation.
They are not customer records or evidence of market demand. These selected files
are tracked in GitHub and excluded from registry/runtime bundles.

## Purpose and scope

Validate a bounded user situation: a project delivery owner has approved copy
and needs a professional editable four-page review, within explicit constraints.
Other planning requests check that this focus does not freeze all input, block
supported analysis, force business language onto teaching, or expand a scoped edit.
This scenario is a first validation hypothesis, not a claim that it is the largest
market. Business analysis is one possible report type, not the validation axis.

The change removes contradictory universal assertion-title/narrative instructions,
clarifies explicit content permissions, and retains existing route contracts.
It changes no engine code, task schema, rendering backend or acceptance gate.

## Reproduce

1. Use a compatible tool-capable agent and install the existing project runtime,
   office renderer and Chinese fonts. Load the selected checkout's `SKILL.md`.
2. In separate fresh contexts, give the agent `planning-requests.md` and its
   referenced `approved-project-review.md`. Request planning only. Do not provide
   expected answers or the other checkout's response.
3. Compare each plan with the actual request: exact-copy boundaries, visible
   qualifiers and metric populations, evidence-supported analysis, topic titles,
   page budget, and authorized revision scope. A plan is not a built deck.
4. In a further fresh context, ask the agent to execute the usage request in
   `approved-project-review.md` using the project's create route. Save its source,
   author input, task, command log, actual PPTX/PDF/PNG output and review evidence.
5. Independently read every actual page and the whole-deck view. Check source text
   against task/PPTX/rendered PDF; inspect native objects. On a disposable copy,
   edit native text in the target office application, save, close and reopen.
6. Record failures and assistance as well as successes. Do not infer a quality or
   productivity gain from a single output or reuse another reviewer's identity.

Planning baseline: local commit `f5370f52b0090dd58e933fd1c157dde67319eec8`,
whose tree matches merged main `d8cd51b542f433b287579ea2263892f2d929899f`
(tree `4a3b914635627ba89f99c7d53d3cfb78b847a2d4`). Candidate: this change set.
Fresh agents inherited the active session model; a concrete model identifier and
complete token/cost measurements were not recorded, so no model-specific benchmark
or productivity comparison is claimed.

## Observed planning results

| Request | Baseline | Initial candidate |
| --- | --- | --- |
| A: approved four-page review | Preserved copy, order and page budget; no unsupported conclusion or extra pages. | Same key constraints; explicitly kept required text visible on its page. |
| B: assisted analysis | Supported arithmetic and uncertainty; native stacked-bar wording was ambiguous/unsupported as a data chart. | Supported arithmetic, but visible shorthand expanded this 120-ticket cohort into a whole-month claim. Shape/chart alternatives still needed capability precision. |
| C: two-page teaching handout | Used topic titles and the specified list/process; no business or navigation additions. | Same key behavior. |
| D: one-sentence update | Preserved scope and distinguished the October 15 historical state from October 17 completion. | Same key behavior. |

No request required a blocking content clarification. A separate read-only reviewer
identified the scope error in B and checked current chart capabilities: native
`bar`/`column` are clustered; editable rectangle segments are shapes, not a native
stacked data-series chart. No new chart capability was added.

The guidance now explicitly preserves population, timeframe, units and denominator
in visible labels even when analysis is allowed. A targeted B follow-up retained
the cohort in titles/body/labels and selected supported doughnut/clustered charts.
That follow-up agent accidentally saw other agents' result summaries through a
status query; it is a directed recheck, **not a blind trial or proof of improvement**.
The initial candidate error remains part of this record.

## Actual four-page execution

- Candidate build: `build-d7be7e729fa341a58793f289589d0520`.
- PPTX SHA-256: `c39007a5f999dc966be597316a611ffbf93971a008727425af68dd7cee72ff12`.
- Two actual complete builds; one revision changed phrase wrapping only.
- Exactly four 16:9 pages, 19 native text objects and 27 native shapes; no bitmap
  slide substitution, extra cover, contents, chapter or thanks page.
- All 19 source title/sentence items match task, PPTX and rendered PDF after
  removing whitespace only; source punctuation, figures and qualifiers retained.
- Real font preflight: two requested faces, no flagged result. Actual output uses
  Alibaba PuHuiTi. All four pages rendered to PDF and 1921×1080 PNGs.
- An author-independent root reviewer read all four actual pages and the assembled
  contact sheet, checked all 19 content nodes, and recorded page-specific findings.
  Scope partition, status track, equal-weight alternatives and conditional actions
  remain distinct while titles, margins and type hierarchy remain coherent.
- This is a restrained four-page brief using many rectangular regions. It does
  **not** validate the richness or craft of a complex decorative business deck,
  or demonstrate visual superiority over the baseline. No baseline PPTX was built.
- A disposable exact-candidate copy was opened in LibreOfficeKit. A native title
  was changed from `项目范围` to `范围复核`, saved as PPTX, closed, reopened and read
  through native text selection. Four pages and 46 text/shape objects remained;
  the original candidate hash did not change. The sampled edit check passed.
- `review` and `deliver` returned `final_delivery_ready` with no blockers and the
  existing `OS_ISOLATION_NOT_VERIFIED` warning. Execution used the existing host
  policy; no gate was disabled or weakened.

Environment: Linux x86_64, Python 3.12.14, python-pptx 1.0.2, Pillow 11.3.0,
jsonschema 4.25.1, lxml 6.1.1; LibreOfficeDev 26.8.0.0.alpha0 build
`2c87e51eeaa2b413ff4ae097b2705eea1995d8e5` and Poppler. The first system-Python
attempt failed due to missing jsonschema; execution continued with a pre-existing
project virtual environment. No dependencies were installed. This is not a clean
installation test or a stable-office compatibility certification. Only one native
text edit was sampled; PowerPoint, WPS, chart/table editing and saved-copy visual
fidelity were not tested. There are no chart/table objects in this fixture.

## Repository checks and conclusion

- Skill and identity validation passed; version remains 5.2.1.
- Seven existing composition-diagnostics regressions passed using the existing
  project virtual environment; these do not test semantic preservation.
- Independent documentation review found no unresolved runtime-contract conflict.
  It identified ignored fixtures; narrow Git exceptions now preserve only the
  selected synthetic prompts and this record, while registry exclusion remains.
- Staged public bundle audit passed: 323 files, 0 errors, 0 warnings (5 existing
  suppressed findings). The new task guidance is included; tests/ and synthetic
  fixtures remain excluded. Final whitespace/diff checks passed.

Retain this bounded clarification and the reproducible prompts. The planning
comparison does **not** establish an overall improvement; one initial candidate
regression was found and recorded. Actual execution supports this short,
explicitly constrained create task, not all routes or user scenarios. Real-user
adoption, complex business/visual outcomes, time/cost savings and broader editing
remain unvalidated. Select the next iteration from observed task failures and user
feedback rather than treating the remaining work packages as mandatory stages.

## Follow-up: update an already delivered task

The next bounded user task uses [revision-request.md](revision-request.md) with
the saved, delivered four-page task above. It updates project dates/status and
directly related next steps; it is not another visual redesign or a real company
record. A fresh author received the raw baseline task and update record, without
the expected changes or other agents' findings.

- Two guarded patches and two complete builds produced the final candidate
  `build-e4c63b99bc904164885596efe8cb71d6`; PPTX SHA-256
  `625aa4f97e2b7ba3ec57c030fefe5d92f2d5da8adc530ab5440a4937ff42a87c`.
- Four visible content records, related provenance/notes and two progress-marker
  colours changed. All object geometry, typography, titles and page order stayed
  fixed. The other 15 visible records were unchanged; pages 1 and 3 had identical
  native slide XML and rendered pixels to the approved baseline.
- The first update made one progress sentence too close to a divider. A second
  patch shortened that updated sentence while preserving planned/actual dates;
  the completed-review detail remains in notes. An initial absolute `--file`
  argument was rejected; the author used the documented task-relative path.
- Fourteen source/scope/output checks passed. The scope check was corrected to
  allow status-marker colour changes: preserving layout does not require an
  obsolete visual status. The earlier overstrict assertion is retained privately.
- Formal review inheritance reused only pages 1 and 3. An independent reviewer
  inspected all four actual pages and 19 bindings, reviewed changed pages 2/4 and
  the assembled deck, and preserved the inherited observations and identity.
  A small difference between the two completed-state markers was non-blocking;
  readable text states both are complete.
- A disposable exact-candidate copy was edited in LibreOfficeKit on page 4:
  `10月20日` became `10月21日`, then saved, closed, reopened and read natively.
  The production copy kept `10月20日`; its hash and 46 native objects were retained.
  The first read-only XML check falsely failed because Office split the date into
  multiple runs. Joining runs within each paragraph fixed the local test helper;
  a fresh actual edit passed. The original failed-check record was not overwritten.
- `review`/`deliver` passed with the existing `OS_ISOLATION_NOT_VERIFIED` warning.
  No runtime, schema or gate change was necessary for this request. The scenario
  and results remain excluded from the runtime distribution.

This establishes one scoped revision of a saved PPT Smith task, not arbitrary
third-party PPTX editing, chart-data updates, long-term reuse, aesthetic superiority
or PowerPoint/WPS compatibility. It reuses a configured environment; installation,
total time/cost and external-user success were not measured.

One follow-up remains: this task reached revision 3 of budget 3. Current `build`
counts every parent-linked build toward the same budget; CLI has no dedicated
new-request cycle. Code inspection confirms the next linked build would reject,
but that rejection was not invoked as an extra build in this run. Do not raise the
budget or drop the parent to disguise unresolved rework. A new, distinct request
after formal delivery needs a documented transition that preserves constraints,
lineage and fresh review; that transition was not implemented or end-to-end
validated here. Resolve this bounded workflow issue before claiming ongoing reuse.

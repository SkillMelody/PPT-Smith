# Template Route Content Integrity Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a source-backed, fail-closed content-integrity foundation to the V4 Template route so incomplete manuscripts and generic placeholder copy cannot become verified delivery candidates.

**Architecture:** Build a deterministic evidence ledger from `SourceDoc`, validate per-slide content contracts against that ledger, calculate evidence-specific coverage, and apply a Template-only hard gate before component planning and again before strict delivery. Preserve source references through strict-preview IR, then replace path-complete template asset checking with output-reachable asset checking.

**Tech Stack:** Python 3.11+, standard library dataclasses/hashlib/json/zipfile/XML, pytest, python-pptx test fixtures, existing PPT Smith `SourceDoc`, provenance, manuscript planner, strict preview, and strict-template pipeline.

**Spec:** `docs/superpowers/specs/2026-09-02-template-route-content-integrity-design.md`

## Global Constraints

- Work only in the task's registered `<write-root>` on branch `feat/v4-template-route-isolation`.
- Run the workspace's registered `verify-task-workspace.sh` gate for the task before every new write phase.
- Keep Standard and Bespoke behavior unchanged; all new fail-closed policy is explicitly Template-scoped.
- Use test-first red-green-refactor for every production behavior.
- Preserve existing public `coverage_report()` behavior for Standard compile callers.
- Diagnostic previews may carry `组件待补充`; delivery candidates may not carry generic copy.
- Do not publish, push, merge, delete worktrees, or modify the pre-existing untracked `.t/` directory.

---

### Task 1: Deterministic Evidence Ledger

**Files:**
- Create: `engine/evidence_ledger.py`
- Create: `tests/unit/test_evidence_ledger.py`

**Interfaces:**
- Consumes: `dict[str, SourceDoc]` and optional `dict[str, str]` source hashes.
- Produces: `build_evidence_ledger(docs, source_hashes=None) -> dict`, `evidence_by_id(ledger) -> dict[str, dict]`, and `validate_evidence_ledger(ledger) -> list[dict]`.

- [ ] **Step 1: Write failing evidence-ledger tests**

```python
from engine.evidence_ledger import build_evidence_ledger, validate_evidence_ledger
from engine.structural_parser import parse_markdown


def test_evidence_ledger_builds_stable_source_backed_units() -> None:
    doc = parse_markdown("# Report\n\n## Growth\n\nRevenue rose 36%.\n\n| Region | Growth |\n|---|---|\n| Global | 52% |", "src")
    first = build_evidence_ledger({"src": doc}, {"src": "sha256:fixed"})
    second = build_evidence_ledger({"src": doc}, {"src": "sha256:fixed"})

    assert first == second
    assert first["sources"] == [{"source_id": "src", "sha256": "sha256:fixed"}]
    units = {unit["evidence_id"]: unit for unit in first["evidence_units"]}
    assert units["src:para_1"]["kind"] == "metric"
    assert units["src:para_1"]["numbers"] == [{"value": "36%", "unit": "%", "period": None}]
    assert units["src:para_1"]["must_keep"] is True
    assert units["src:table_1"]["kind"] == "exhibit"
    assert units["src:table_1"]["exhibit_id"] == "src:table_1"
    assert validate_evidence_ledger(first) == []


def test_evidence_ledger_rejects_duplicate_ids_and_dangling_anchors() -> None:
    ledger = {
        "schema_version": "1.0.0",
        "sources": [{"source_id": "src", "sha256": "sha256:fixed"}],
        "evidence_units": [{
            "evidence_id": "src:para_99",
            "source_ref": {"source_id": "src", "loc": "para_99"},
            "kind": "claim",
            "text": "missing",
            "entities": [],
            "numbers": [],
            "relations": [],
            "salience": 1.0,
            "must_keep": False,
            "exhibit_id": None,
        }] * 2,
    }

    codes = {issue["code"] for issue in validate_evidence_ledger(ledger)}
    assert codes == {"EVIDENCE_ID_DUPLICATE"}
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m pytest -q tests/unit/test_evidence_ledger.py --maxfail=1`

Expected: collection fails with `ModuleNotFoundError: No module named 'engine.evidence_ledger'`.

- [ ] **Step 3: Implement the ledger**

```python
def build_evidence_ledger(
    docs: dict[str, SourceDoc],
    source_hashes: dict[str, str] | None = None,
) -> dict:
    sources = []
    units = []
    for source_id, doc in docs.items():
        digest = (source_hashes or {}).get(source_id) or _source_digest(doc)
        sources.append({"source_id": source_id, "sha256": digest})
        for element in doc.elements:
            if element.etype.startswith("h") or not element.full_text():
                continue
            kind = _kind(element)
            numbers = [_number_record(value) for value in sorted(element.numbers())]
            units.append({
                "evidence_id": f"{source_id}:{element.anchor}",
                "source_ref": {"source_id": source_id, "loc": element.anchor},
                "kind": kind,
                "text": element.full_text(),
                "entities": [],
                "numbers": numbers,
                "relations": [],
                "salience": 3.0 if kind == "exhibit" else 2.0 if kind == "metric" else 1.0,
                "must_keep": kind in {"metric", "exhibit"},
                "exhibit_id": f"{source_id}:{element.anchor}" if kind == "exhibit" else None,
            })
    return {"schema_version": "1.0.0", "sources": sources, "evidence_units": units}
```

The validator checks schema shape, unique IDs, source membership, valid anchor grammar, positive salience, allowed kinds, and exhibit consistency. It returns stable issue dictionaries and does not raise for user data.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `python3 -m pytest -q tests/unit/test_evidence_ledger.py`

Expected: all tests pass.

- [ ] **Step 5: Commit Task 1**

```bash
git add engine/evidence_ledger.py tests/unit/test_evidence_ledger.py
git commit -m "feat(template): add deterministic evidence ledger"
```

---

### Task 2: Slide Content Contracts and Evidence Coverage

**Files:**
- Create: `engine/content_contract.py`
- Modify: `engine/coverage.py`
- Create: `tests/unit/test_content_contract.py`
- Modify: `tests/unit/test_engine_p2.py`

**Interfaces:**
- Consumes: content bindings with `slides[*].assertion`, `archetype`, `evidence_ids`, `required_evidence_ids`, and `omissions`.
- Produces: `validate_content_contracts(content_bindings, ledger) -> list[dict]` and `evidence_coverage_report(content_bindings, ledger) -> dict`.

- [ ] **Step 1: Write failing contract and evidence-coverage tests**

```python
from engine.content_contract import validate_content_contracts
from engine.coverage import evidence_coverage_report


def test_body_contract_requires_assertion_and_known_evidence() -> None:
    ledger = _ledger([_unit("src:para_1", must_keep=True)])
    bindings = {"slides": [{
        "id": "growth",
        "archetype": "body",
        "assertion": "",
        "evidence_ids": ["src:para_99"],
        "required_evidence_ids": ["src:para_1"],
        "omissions": [],
    }]}

    assert {issue["code"] for issue in validate_content_contracts(bindings, ledger)} == {
        "SLIDE_ASSERTION_MISSING", "EVIDENCE_ID_UNKNOWN", "REQUIRED_EVIDENCE_MISSING",
    }


def test_evidence_coverage_reports_weighted_numeric_and_exhibit_recall() -> None:
    ledger = _ledger([
        _unit("src:para_1", kind="metric", salience=2.0, must_keep=True),
        _unit("src:table_1", kind="exhibit", salience=3.0, must_keep=True, exhibit_id="src:table_1"),
        _unit("src:para_2", kind="claim", salience=1.0),
    ])
    bindings = {"slides": [{
        "id": "growth",
        "archetype": "body",
        "assertion": "Revenue increased",
        "evidence_ids": ["src:para_1"],
        "required_evidence_ids": ["src:para_1"],
        "omissions": [{"evidence_id": "src:table_1", "reason": "Appendix exhibit"}],
    }]}

    report = evidence_coverage_report(bindings, ledger)
    assert report["weighted_ratio"] == 0.3333
    assert report["required_ratio"] == 1.0
    assert report["numeric_ratio"] == 1.0
    assert report["exhibit_ratio"] == 1.0
    assert report["uncovered_evidence_ids"] == ["src:para_2"]
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m pytest -q tests/unit/test_content_contract.py tests/unit/test_engine_p2.py --maxfail=1`

Expected: import failure for `engine.content_contract` or missing `evidence_coverage_report`.

- [ ] **Step 3: Implement validation and evidence coverage**

`validate_content_contracts()` validates slide IDs, archetypes, assertions, evidence IDs, required evidence IDs, and non-empty omission reasons. Cover, section, and closing archetypes may omit evidence only when explicitly identified; body/data/method slides may not.

`evidence_coverage_report()` treats an exhibit with a documented omission as handled for exhibit coverage but not as selected for weighted coverage. Ratios round to four decimal places. Empty denominators return `1.0`.

- [ ] **Step 4: Run focused tests and existing coverage regression**

Run: `python3 -m pytest -q tests/unit/test_content_contract.py tests/unit/test_engine_p2.py`

Expected: all tests pass, including the unchanged section/table coverage test.

- [ ] **Step 5: Commit Task 2**

```bash
git add engine/content_contract.py engine/coverage.py tests/unit/test_content_contract.py tests/unit/test_engine_p2.py
git commit -m "feat(template): add slide content contracts and evidence coverage"
```

---

### Task 3: Template Content-Integrity Hard Gate

**Files:**
- Create: `engine/content_integrity_gate.py`
- Modify: `engine/manuscript_component_planner.py`
- Modify: `engine/__main__.py`
- Create: `tests/unit/test_content_integrity_gate.py`
- Modify: `tests/unit/test_manuscript_component_planner.py`

**Interfaces:**
- Produces: `evaluate_template_content_integrity(content_bindings, ledger, policy=None) -> dict`.
- Changes: `build_manuscript_component_composition(atlas, content_bindings, storyboard, *, evidence_ledger=None, enforce_content_integrity=False)`.
- CLI: `plan-manuscript-components --evidence-ledger LEDGER.json --delivery-candidate` enables fail-closed mode.

- [ ] **Step 1: Write failing gate tests**

```python
from engine.content_integrity_gate import evaluate_template_content_integrity


def test_gate_rejects_missing_required_and_low_weighted_coverage() -> None:
    result = evaluate_template_content_integrity(
        _bindings(selected=["src:para_2"]),
        _ledger(required="src:para_1"),
    )

    assert result["status"] == "fail"
    assert {issue["code"] for issue in result["issues"]} >= {
        "REQUIRED_EVIDENCE_MISSING", "WEIGHTED_COVERAGE_BELOW_FLOOR",
    }


def test_delivery_planner_refuses_without_evidence_ledger() -> None:
    with pytest.raises(ValueError, match="CONTENT_INTEGRITY_LEDGER_REQUIRED"):
        build_manuscript_component_composition(
            _atlas(), _bindings(), _storyboard(), enforce_content_integrity=True,
        )
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m pytest -q tests/unit/test_content_integrity_gate.py tests/unit/test_manuscript_component_planner.py --maxfail=1`

Expected: missing module or unsupported keyword argument.

- [ ] **Step 3: Implement the gate and planner integration**

```python
DEFAULT_TEMPLATE_CONTENT_POLICY = {
    "weighted_ratio": 0.90,
    "required_ratio": 1.0,
    "numeric_ratio": 0.95,
    "exhibit_ratio": 1.0,
}


def evaluate_template_content_integrity(content_bindings, ledger, policy=None):
    effective = {**DEFAULT_TEMPLATE_CONTENT_POLICY, **(policy or {})}
    contract_issues = validate_content_contracts(content_bindings, ledger)
    coverage = evidence_coverage_report(content_bindings, ledger)
    issues = [*contract_issues, *_coverage_issues(coverage, effective)]
    return {"status": "pass" if not issues else "fail", "policy": effective,
            "coverage": coverage, "issues": issues}
```

The planner evaluates the gate before route selection when `enforce_content_integrity=True`. On failure it raises `ValueError` beginning with `CONTENT_INTEGRITY_FAILED:` and includes stable issue codes. The composition includes the passing report under `content_integrity`.

The CLI requires `--evidence-ledger` when `--delivery-candidate` is supplied. Preview callers remain backward compatible and are explicitly labeled with `content_integrity.status = "not_enforced"`.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `python3 -m pytest -q tests/unit/test_content_integrity_gate.py tests/unit/test_manuscript_component_planner.py`

Expected: all tests pass.

- [ ] **Step 5: Commit Task 3**

```bash
git add engine/content_integrity_gate.py engine/manuscript_component_planner.py engine/__main__.py tests/unit/test_content_integrity_gate.py tests/unit/test_manuscript_component_planner.py
git commit -m "feat(template): enforce content integrity before delivery planning"
```

---

### Task 4: Remove Generic Delivery Copy

**Files:**
- Modify: `engine/manuscript_component_planner.py`
- Modify: `engine/content_integrity_gate.py`
- Modify: `tests/unit/test_manuscript_component_planner.py`
- Modify: `tests/unit/test_content_integrity_gate.py`

**Interfaces:**
- Changes `_label_text()` to reject missing semantic labels instead of generating position-based copy.
- Adds delivery scan issue `GENERIC_DELIVERY_LABEL` for exact and numbered variants.

- [ ] **Step 1: Write failing generic-copy tests**

```python
def test_extended_component_requires_explicit_semantic_labels() -> None:
    with pytest.raises(ValueError, match="requires explicit label field 'title'"):
        build_manuscript_component_composition(
            _atlas(), _bindings_with_string_items(), _storyboard(),
        )


@pytest.mark.parametrize("text", ["要点 1", "顺序", "核心议题", "阶段 3"])
def test_delivery_gate_rejects_generic_copy(text: str) -> None:
    bindings = _complete_bindings()
    bindings["slides"][0]["items"] = [{"title": text, "detail": "source-backed detail"}]
    result = evaluate_template_content_integrity(bindings, _complete_ledger())
    assert any(issue["code"] == "GENERIC_DELIVERY_LABEL" for issue in result["issues"])
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m pytest -q tests/unit/test_manuscript_component_planner.py tests/unit/test_content_integrity_gate.py --maxfail=1`

Expected: planner still generates `要点 1` or gate does not detect generic copy.

- [ ] **Step 3: Replace fallback generation with explicit-label validation**

`detail` may use the item's source-backed text. `title`, `badge`, `metric_label`, and `metric_value` must be explicitly supplied whenever the reviewed component declares those fields. Cover subtitle splitting no longer creates `核心议题`; delivery bindings must provide structured items.

Update old tests and fixtures to use meaningful explicit labels such as `采用率`, `规模化`, and `试验阶段`. Do not replace one generic token with another.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `python3 -m pytest -q tests/unit/test_manuscript_component_planner.py tests/unit/test_content_integrity_gate.py`

Expected: all tests pass and no test expects generated `要点`, `顺序`, or `核心议题`.

- [ ] **Step 5: Commit Task 4**

```bash
git add engine/manuscript_component_planner.py engine/content_integrity_gate.py tests/unit/test_manuscript_component_planner.py tests/unit/test_content_integrity_gate.py
git commit -m "fix(template): reject generic delivery copy"
```

---

### Task 5: Preserve Source References Through Strict Preview

**Files:**
- Modify: `engine/manuscript_component_planner.py`
- Modify: `engine/manuscript_strict_preview.py`
- Modify: `tests/unit/test_manuscript_strict_preview.py`

**Interfaces:**
- Planner element labels carry `source_ref` from their content-binding item.
- Strict-preview IR items retain `source_ref` and slide-level evidence IDs.
- Preview summary adds `evidence_units` and `source_references` counts.

- [ ] **Step 1: Write failing source-propagation test**

```python
def test_preview_bundle_preserves_item_source_refs_and_evidence_counts() -> None:
    operation = _component_operation(labels=[{
        "text": "Revenue increased 36%",
        "binding_name": "bind:block:growth:component_items:item:0",
        "source_ref": {"source_id": "src", "loc": "para_1"},
        "evidence_id": "src:para_1",
    }])
    bundle = build_manuscript_strict_preview_bundle(
        content_bindings=_source_bound_bindings(), storyboard=_storyboard(),
        composition=_composition(), component_plan={"operations": [operation]},
    )

    item = bundle["ir"]["slides"][0]["blocks"][0]["items"][0]
    assert item["source_ref"] == {"source_id": "src", "loc": "para_1"}
    assert item["evidence_id"] == "src:para_1"
    assert bundle["summary"]["evidence_units"] == 1
    assert bundle["summary"]["source_references"] == 1
```

- [ ] **Step 2: Run test and verify RED**

Run: `python3 -m pytest -q tests/unit/test_manuscript_strict_preview.py::test_preview_bundle_preserves_item_source_refs_and_evidence_counts`

Expected: item lacks `source_ref` or summary lacks evidence counts.

- [ ] **Step 3: Implement metadata propagation**

Extend `_add_component_binding()` with optional `source_ref` and `evidence_id`, reject conflicting metadata for the same item, and copy metadata from planner labels/text bindings. Count unique evidence IDs and canonical `(source_id, loc)` pairs after IR assembly.

- [ ] **Step 4: Run preview and planner tests**

Run: `python3 -m pytest -q tests/unit/test_manuscript_strict_preview.py tests/unit/test_manuscript_component_planner.py`

Expected: all tests pass.

- [ ] **Step 5: Commit Task 5**

```bash
git add engine/manuscript_component_planner.py engine/manuscript_strict_preview.py tests/unit/test_manuscript_strict_preview.py
git commit -m "feat(template): preserve evidence references in strict preview"
```

---

### Task 6: Enforce Content Integrity at Strict Delivery

**Files:**
- Modify: `engine/strict_template.py`
- Modify: `tests/unit/test_strict_template.py`

**Interfaces:**
- Changes `execute_strict_template(..., evidence_ledger: dict | None = None, content_bindings: dict | None = None)`.
- Returns `CONTENT_INTEGRITY_REQUIRED` or `CONTENT_INTEGRITY_FAILED` before applying native operations.

- [ ] **Step 1: Write failing strict-delivery test**

```python
def test_strict_delivery_rejects_missing_content_integrity_inputs(template_pptx, tmp_path) -> None:
    result = execute_strict_template(
        request=_template_request(template_pptx), template_pptx=template_pptx,
        strict_plan=_strict_plan(), ir=_ir(), source_docs=_source_docs(),
        output_pptx=tmp_path / "candidate.pptx",
    )
    assert result == {"ok": False, "code": "CONTENT_INTEGRITY_REQUIRED"}
```

- [ ] **Step 2: Run test and verify RED**

Run: `python3 -m pytest -q tests/unit/test_strict_template.py::test_strict_delivery_rejects_missing_content_integrity_inputs`

Expected: strict delivery proceeds past the missing inputs.

- [ ] **Step 3: Add the strict-delivery gate**

Run `evaluate_template_content_integrity()` after route/template hash validation and before creating the temporary working copy. Include the passing report in the final result as `content_integrity`. Existing low-level strict-template tests that intentionally test shape mechanics pass complete minimal ledger/binding fixtures.

- [ ] **Step 4: Run strict-template tests**

Run: `python3 -m pytest -q tests/unit/test_strict_template.py`

Expected: all tests pass.

- [ ] **Step 5: Commit Task 6**

```bash
git add engine/strict_template.py tests/unit/test_strict_template.py
git commit -m "feat(template): gate strict delivery on content integrity"
```

---

### Task 7: Reachable Asset Preservation

**Files:**
- Modify: `engine/strict_template.py`
- Modify: `tests/unit/test_strict_template.py`

**Interfaces:**
- Replaces path-complete `_asset_preservation()` with output-reachable preservation.
- Returns `verified_parts`, `changed_parts`, and `broken_relationships`.

- [ ] **Step 1: Write failing asset tests**

```python
def test_asset_preservation_ignores_unreachable_source_media(tmp_path: Path) -> None:
    source = _pptx_zip(tmp_path / "source.pptx", media={"image1.png": b"used", "image2.png": b"unused"})
    output = _pptx_zip(tmp_path / "output.pptx", media={"image1.png": b"used"})
    assert _asset_preservation(source, output)["status"] == "pass"


def test_asset_preservation_rejects_changed_output_media(tmp_path: Path) -> None:
    source = _pptx_zip(tmp_path / "source.pptx", media={"image1.png": b"original"})
    output = _pptx_zip(tmp_path / "output.pptx", media={"image1.png": b"changed"})
    report = _asset_preservation(source, output)
    assert report["status"] == "fail"
    assert report["changed_parts"] == ["ppt/media/image1.png"]
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m pytest -q tests/unit/test_strict_template.py -k 'asset_preservation_ignores or asset_preservation_rejects' --maxfail=1`

Expected: the first test fails because `image2.png` is missing from the output.

- [ ] **Step 3: Implement output-reachable checking**

Compare every output part under `ASSET_PREFIXES` with the same source part. Parse output `.rels` XML, resolve internal targets with POSIX path normalization, and report asset relationships whose targets are absent. Do not require source-only assets that have no output relationship or output part.

- [ ] **Step 4: Run strict-template tests**

Run: `python3 -m pytest -q tests/unit/test_strict_template.py`

Expected: all tests pass.

- [ ] **Step 5: Commit Task 7**

```bash
git add engine/strict_template.py tests/unit/test_strict_template.py
git commit -m "fix(template): verify only delivery-reachable assets"
```

---

### Task 8: Reproducible Integration Boundary and Acceptance Regression

**Files:**
- Create: `tests/integration/test_template_content_integrity.py`
- Modify: `tests/integration/test_real_component_atlas.py`
- Modify: `docs/v4-template-route.md`

**Interfaces:**
- Adds a generated, repository-local Template integration fixture for content-integrity behavior.
- Makes McKinsey-specific reference-atlas tests explicitly optional through `PPT_SMITH_MCKINSEY_FIXTURE`, with a module-level skip when the named directory is unavailable.

- [ ] **Step 1: Write failing generated integration test**

```python
def test_template_delivery_rejects_middle_section_omission(tmp_path: Path) -> None:
    docs = {"src": parse_markdown(_THREE_SECTION_REPORT, "src")}
    ledger = build_evidence_ledger(docs)
    bindings = _bindings_selecting_first_and_last_sections_only(ledger)
    result = evaluate_template_content_integrity(bindings, ledger)
    assert result["status"] == "fail"
    assert "src:para_2" in result["coverage"]["missing_required_evidence_ids"]
```

- [ ] **Step 2: Run integration tests and verify current fixture failure**

Run: `python3 -m pytest -q tests/integration/test_template_content_integrity.py tests/integration/test_real_component_atlas.py --maxfail=1`

Expected: generated test initially fails before file implementation, and the McKinsey module currently fails with `FileNotFoundError` when its external fixture is absent.

- [ ] **Step 3: Add generated integration fixture and explicit reference-fixture routing**

Use `os.environ.get("PPT_SMITH_MCKINSEY_FIXTURE")` when provided; otherwise use the historical repository path only if it exists. Apply `pytestmark = pytest.mark.skipif(PROJECT is None, reason="McKinsey reference fixture not installed")`. The generated content-integrity integration test must always run and cannot be skipped.

Document the environment variable, the distinction between always-on generated integration coverage and optional proprietary reference-atlas coverage, and the delivery-candidate ledger requirement.

- [ ] **Step 4: Run integration and focused Template suites**

Run: `python3 -m pytest -q tests/integration/test_template_content_integrity.py tests/integration/test_real_component_atlas.py`

Expected: generated integration tests pass; McKinsey tests either pass with the configured fixture or are explicitly skipped as a group.

Run: `python3 -m pytest -q tests/unit/test_evidence_ledger.py tests/unit/test_content_contract.py tests/unit/test_content_integrity_gate.py tests/unit/test_engine_p2.py tests/unit/test_manuscript_component_planner.py tests/unit/test_manuscript_strict_preview.py tests/unit/test_strict_template.py tests/integration/test_template_content_integrity.py`

Expected: all selected tests pass with zero failures.

- [ ] **Step 5: Commit Task 8**

```bash
git add tests/integration/test_template_content_integrity.py tests/integration/test_real_component_atlas.py docs/v4-template-route.md
git commit -m "test(template): make content integrity integration reproducible"
```

---

### Task 9: Full Verification and Fixed 30-Page Baseline Rejection

**Files:**
- Modify only if a failing regression exposes a defect covered by this spec; add a failing regression test before the fix.
- Create: `test-runs/template-content-integrity-subproject-a-20260902/reports/subproject-a-verification.json`

**Interfaces:**
- Produces fresh verification evidence and a machine-readable report; does not produce a deliverable PPTX.

- [ ] **Step 1: Run formatting and focused verification**

Run: `git diff --check`

Expected: no output and exit code 0.

Run: `python3 -m pytest -q tests/unit/test_evidence_ledger.py tests/unit/test_content_contract.py tests/unit/test_content_integrity_gate.py tests/unit/test_engine_p2.py tests/unit/test_manuscript_component_planner.py tests/unit/test_manuscript_strict_preview.py tests/unit/test_strict_template.py tests/integration/test_template_content_integrity.py`

Expected: zero failures.

- [ ] **Step 2: Run the broader Template-focused suite**

Run: `python3 -m pytest -q tests/unit/test_template_native.py tests/unit/test_strict_template.py tests/unit/test_component_atlas.py tests/unit/test_component_inventory.py tests/unit/test_component_composer.py tests/unit/test_manuscript_component_planner.py tests/unit/test_manuscript_strict_preview.py tests/unit/test_route_isolation.py tests/unit/test_template_evidence.py tests/unit/test_template_request.py tests/unit/test_evidence_ledger.py tests/unit/test_content_contract.py tests/unit/test_content_integrity_gate.py tests/integration/test_template_content_integrity.py`

Expected: zero failures.

- [ ] **Step 3: Exercise the fixed 30-page content bindings against the hard gate**

Build an evidence ledger from the accepted source-anchor representation, run the existing 30-page content bindings as a delivery candidate, and save the gate report. The expected outcome is `status=fail` with required/weighted/numeric evidence issues; Subproject A proves rejection, not a regenerated high-quality deck.

- [ ] **Step 4: Record verification evidence**

The JSON report records commit, commands, exit codes, pass/fail/skip counts, gate policy, 30-page gate issue codes, and the unchanged source/template hashes. It must not claim Subprojects B or C are implemented.

- [ ] **Step 5: Commit verification report**

```bash
git add test-runs/template-content-integrity-subproject-a-20260902/reports/subproject-a-verification.json
git commit -m "test(template): verify content integrity foundation"
```

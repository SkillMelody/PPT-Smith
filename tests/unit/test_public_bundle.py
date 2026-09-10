from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_builder():
    path = ROOT / "scripts" / "build_public_bundle.py"
    spec = importlib.util.spec_from_file_location("build_public_bundle", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_registry_ignore_rules_exclude_private_and_development_content() -> None:
    builder = load_builder()
    rules = builder.ignore_rules()
    assert builder.ignored("private-pmo-pack/contracts/x.json", rules)
    assert builder.ignored("tests/unit/test_x.py", rules)
    assert builder.ignored("test-runs/user/deck.pptx", rules)
    assert builder.ignored("runtime/pptxgenjs/node_modules/pptxgenjs/index.js", rules)
    assert not builder.ignored("engine/strict_template.py", rules)
    assert not builder.ignored("requirements.txt", rules)


def test_audit_timestamp_can_be_fixed_for_reproducible_archives(monkeypatch) -> None:
    audit_path = ROOT / "scripts" / "audit_bundle.py"
    spec = importlib.util.spec_from_file_location("audit_bundle", audit_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv("PPTSMITH_AUDIT_TIMESTAMP", "2026-09-09T00:00:00+00:00")
    assert module.iso_now() == "2026-09-09T00:00:00+00:00"

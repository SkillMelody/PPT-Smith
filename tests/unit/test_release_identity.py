from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_public_release_identity_is_consistent() -> None:
    checker = load_script("check_identity.py")
    assert checker.check(ROOT) == []


def test_public_release_excludes_private_pack() -> None:
    assert not (ROOT / "private-pmo-pack").exists()
    assert "private-pmo-pack/" in (ROOT / ".clawhubignore").read_text(encoding="utf-8")
    assert "private-pmo-pack/" in (ROOT / "packaging" / "bundle-exclude.txt").read_text(encoding="utf-8")


def test_release_dependency_manifests_are_pinned() -> None:
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    assert requirements
    assert all("==" in line for line in requirements if line and not line.startswith("#"))
    runtime = json.loads((ROOT / "runtime" / "pptxgenjs" / "package.json").read_text(encoding="utf-8"))
    assert runtime["private"] is True
    assert all(not value.startswith(("^", "~")) for value in runtime["dependencies"].values())


def test_audit_allowlist_entries_are_reasoned() -> None:
    document = json.loads((ROOT / "packaging" / "audit-allowlist.json").read_text(encoding="utf-8"))
    entries = document["allowlist"]
    assert entries
    for entry in entries:
        assert entry.get("path")
        assert entry.get("codes")
        assert entry.get("reason")


def test_skill_entrypoint_has_no_unfinished_frontmatter() -> None:
    validator = load_script("quick_validate_skill.py")
    assert validator.main() == 0

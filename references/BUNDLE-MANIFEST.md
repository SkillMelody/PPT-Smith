# PPT Smith Public Bundle Manifest

## Identity

- Display name: MeowClaw PPT Smith
- Installed route: `article-html-to-ppt`
- Public slug: `meowclaw-pptsmith`
- Version: `5.1.0-dev.1`
- License: Apache-2.0

`VERSION` and `packaging/identity.json` are the machine-readable identity source.
Run `python3 scripts/check_identity.py` before packaging.

## Included public capability

- `SKILL.md` and route documentation;
- declarative create/recreate, compact authoring, and verified revision modules;
- native Template and legacy Bespoke/Standard engine modules;
- public schemas, styles, templates, and component contracts;
- deterministic builders and QA tooling;
- the lockfile-pinned PptxGenJS runtime source;
- selected public sample images, editable sample PPTX, measured evidence, and current operating references.

## Excluded material

The public bundle excludes:

- private PMO and enterprise production packs;
- raw user inputs, local test runs, private customer decks, and review transcripts;
- dependency caches and virtual environments;
- credentials, local environment files, and machine-specific paths;
- development-only tests and CI configuration from the ClawHub package.

The source repository may retain public tests and CI. `.clawhubignore` defines
the smaller registry distribution boundary; `.gitattributes` defines export
exclusions for source archives.

## Required release checks

```bash
python3 scripts/check_identity.py
python3 scripts/quick_validate_skill.py
python3 scripts/bootstrap_pptxgenjs_runtime.py --check
python3 -m pytest -q
python3 scripts/audit_bundle.py --mode worktree --check --fail-on-finding
```

Public release is fail-closed: a dirty release tree, identity drift, a bundle
audit error, failed test, or missing acceptance report blocks publication.

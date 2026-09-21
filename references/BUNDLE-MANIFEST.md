# PPT Smith Public Bundle Manifest

## Identity

- Display name: MeowClaw PPT Smith
- Installed route: `article-html-to-ppt`
- Public slug: `meowclaw-pptsmith`
- Version: `5.1.0`
- License: Apache-2.0

`VERSION` and `packaging/identity.json` define the release identity.

## Included material

GitHub, ClawHub and other public distributions contain material needed to
install, use, inspect and package the Skill:

- `SKILL.md`, README usage instructions and route references;
- runtime engine, native builders, rendering and delivery QA tools;
- dependency declarations and the pinned PptxGenJS runtime source;
- schemas, reusable styles, templates and valid authoring examples;
- branding and selected sample previews, editable PPTX files and concise object data;
- identity and distribution checks that keep the package self-contained.

The v5.0 20-slide research example and v5.1 six-slide policy example retain
separate counts and original file hashes. A replaceable bitmap is not counted
as an internally editable native object.

## Local-only material

Development tests and fixtures, CI, benchmark harnesses, development notes,
promotional articles, source PDFs, full review/edit logs, intermediate builds,
worktrees, caches, credentials and private customer/commercial materials are
excluded from the public source tree and registry bundle. Local files are
preserved for development. Exclusion does not rewrite earlier published history.

`.gitignore` prevents normal staging of local-only files. `.clawhubignore`
filters registry packaging, `.gitattributes` filters source exports, and
`packaging/bundle-exclude.txt` makes their presence fail the archive audit.
Only intentionally selected usage examples belong in `assets/samples/`.

## Checks

```bash
python3 scripts/check_identity.py
python3 scripts/quick_validate_skill.py
python3 -m engine design capabilities
```

The public bundle builder audits the exact selected tree before creating the
ZIP. Its detailed audit reports and archive manifest stay beside the local
packaging output; the ZIP contains runtime and usage material. The package
version does not by itself mean any external platform has been updated.

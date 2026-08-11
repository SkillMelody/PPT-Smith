"""PPT Smith v4 engine: deterministic presentation compiler core.

The engine owns everything downstream of the Presentation IR contract
(schemas/v4/): source parsing, extractive fallback IR, provenance
verification, coverage checks, design policy, layout, rendering, and QA.
The LLM's only job is to produce an IR; the engine's job is to make a
deck out of it — deterministically.

Stdlib-only by design so it ships inside the skill, mirroring
scripts/validate_contracts.py.
"""

__version__ = "4.0.0-dev"

IR_SCHEMA_VERSION = "4.0.0"

"""Coverage checker: how much of the source does an IR actually use?

Guards against the weak-model failure of "read half the article and stop"
(plan decision D5). Coverage is computed structurally: each section of the
source (h2 outline by default) counts as covered when any anchor inside it
is referenced by the IR; tables are tracked individually because dropped
tables are the most common silent content loss.

The report is advisory data — thresholds and pass/fail policy belong to the
pipeline (P3), not here. `status` is a suggestion computed from default
thresholds so CLI users get a signal without extra wiring.
"""

from __future__ import annotations

from .source_doc import SourceDoc, parse_anchor

DEFAULT_SECTION_THRESHOLD = 0.6
DEFAULT_TABLE_THRESHOLD = 1.0


def _referenced_anchors(ir: dict) -> dict[str, set[str]]:
    refs: dict[str, set[str]] = {}

    def note(ref: dict | None) -> None:
        if not isinstance(ref, dict):
            return
        parsed = parse_anchor(ref.get("loc", ""))
        if parsed is None:
            return
        refs.setdefault(ref.get("source_id", ""), set()).add(f"{parsed[0]}_{parsed[1]}")

    for slide in ir.get("slides", []):
        for block in slide.get("blocks", []):
            note(block.get("source_ref"))
            for multi_ref in block.get("source_refs", []) or []:
                note(multi_ref)
            for item in block.get("items", []) or []:
                note(item.get("source_ref"))
    return refs


def _sections(doc: SourceDoc) -> list[tuple[str, set[str]]]:
    level = 2 if doc.headings(2) else (1 if len(doc.headings(1)) > 1 else None)
    if level is None:
        return [(doc.title() or "(whole document)",
                 {e.anchor for e in doc.elements})]
    sections: list[tuple[str, set[str]]] = []
    title, anchors = "(preamble)", set()
    for element in doc.elements:
        if element.etype == f"h{level}":
            if anchors:
                sections.append((title, anchors))
            title, anchors = element.text, {element.anchor}
        else:
            anchors.add(element.anchor)
    if anchors:
        sections.append((title, anchors))
    return sections


def coverage_report(ir: dict, docs: dict[str, SourceDoc], *,
                    section_threshold: float = DEFAULT_SECTION_THRESHOLD,
                    table_threshold: float = DEFAULT_TABLE_THRESHOLD) -> dict:
    referenced = _referenced_anchors(ir)
    per_source: list[dict] = []
    for source_id, doc in docs.items():
        used = referenced.get(source_id, set())
        sections = _sections(doc)
        covered = [t for t, anchors in sections if anchors & used]
        uncovered = [t for t, anchors in sections if not (anchors & used)]
        tables = [t.anchor for t in doc.tables()]
        tables_covered = [a for a in tables if a in used]
        per_source.append({
            "source_id": source_id,
            "sections_total": len(sections),
            "sections_covered": len(covered),
            "sections_uncovered": uncovered,
            "section_ratio": round(len(covered) / len(sections), 3) if sections else 1.0,
            "tables_total": len(tables),
            "tables_covered": len(tables_covered),
            "tables_uncovered": [a for a in tables if a not in used],
            "table_ratio": round(len(tables_covered) / len(tables), 3) if tables else 1.0,
        })

    worst_section = min((s["section_ratio"] for s in per_source), default=1.0)
    worst_table = min((s["table_ratio"] for s in per_source), default=1.0)
    status = "pass"
    if worst_section < section_threshold or worst_table < table_threshold:
        status = "warn"
    if worst_section < section_threshold / 2:
        status = "fail"
    return {
        "status": status,
        "section_threshold": section_threshold,
        "table_threshold": table_threshold,
        "sources": per_source,
    }

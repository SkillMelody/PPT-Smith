"""Declared composition diagnostics; never infer visual quality or approval."""
from __future__ import annotations

from collections import Counter


def composition_diagnostics(task):
    """Flag repetition for human review without banning intentional sequences.

    A different shape or author-supplied family name does not prove a different
    topology. Reviewers must inspect the actual deck and semantic reading paths.
    Navigation pages interrupt consecutive runs and are excluded from ratios.
    """
    designs = {page["page_id"]: page for page in task["design"]["pages"]}
    body, runs, run, matrix, unplanned = [], [], [], [], []
    previous = None
    for page in task["scene"]["pages"]:
        composition = designs[page["id"]].get("composition")
        row = {"page_id": page["id"], "planning_status": "planned" if composition else "missing"}
        if composition:
            row.update({key: composition[key] for key in ("page_role", "content_relation", "layout_family",
                        "reading_path", "information_attachment", "claim_content_id") if key in composition})
        else:
            unplanned.append(page["id"])
        matrix.append(row)
        key = None
        if composition and composition["page_role"] == "body":
            key = (composition["layout_family"].strip().casefold(), composition["information_attachment"])
            body.append((page["id"], key))
        if key is not None and key == previous:
            run.append(page["id"])
        else:
            if len(run) >= 3:
                runs.append(run)
            run = [page["id"]] if key is not None else []
        previous = key
    if len(run) >= 3:
        runs.append(run)
    warnings = [{"code": "COMPOSITION_REPEATED_SEQUENCE", "page_ids": pages,
                 "message": "Inspect whether the repeated structure supports a deliberate sequence; shape changes alone do not prove variety."}
                for pages in runs]
    if task["design"].get("review_profile") == "decorative_business" and unplanned:
        warnings.insert(0, {"code": "COMPOSITION_PLAN_INCOMPLETE", "page_ids": unplanned,
                            "message": "Complete the page composition plans before building this review profile."})
    counts = Counter(key for _, key in body)
    if len(body) >= 5 and counts:
        dominant, count = counts.most_common(1)[0]
        if count / len(body) >= .6:
            warnings.append({"code": "COMPOSITION_DOMINANT_FAMILY",
                             "page_ids": [pid for pid, key in body if key == dominant],
                             "message": "Review deck rhythm and content fit; this declared family dominates the body pages."})
    return {"status": "diagnostic_only", "automatic_visual_approval": False,
            "body_page_count": len(body), "declared_family_count": len({key[0] for key in counts}),
            "declared_structure_count": len(counts),
            "unplanned_page_ids": unplanned, "pages": matrix,
            "warnings": warnings}

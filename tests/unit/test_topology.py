from __future__ import annotations

from engine.topology import infer_topology


def test_explicit_topology_wins_over_legacy_layout_pattern() -> None:
    result = infer_topology(
        {"topology": "comparison", "items": [{"title": "A"}, {"title": "B"}]},
        {"layout_rationale": {"layout_pattern": "three conclusion cards"}},
    )

    assert result == {"topology": "comparison", "source": "content_binding"}


def test_legacy_pattern_is_classified_only_when_content_has_no_topology() -> None:
    result = infer_topology(
        {"items": [{"title": "One"}, {"title": "Two"}]},
        {"layout_rationale": {"layout_pattern": "risk and mitigation"}},
    )

    assert result == {"topology": "risk_mitigation", "source": "legacy_pattern"}


def test_unknown_or_missing_signals_fail_closed() -> None:
    assert infer_topology({}, {"layout_rationale": {"layout_pattern": "unknown"}}) == {
        "topology": None,
        "source": "unclassified",
    }

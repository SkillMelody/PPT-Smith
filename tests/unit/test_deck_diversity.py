from __future__ import annotations

from engine.deck_diversity import evaluate_family_diversity


def test_diversity_rejects_three_consecutive_component_families() -> None:
    report = evaluate_family_diversity([
        {"family": "card_grid", "archetype": "body"},
        {"family": "card_grid", "archetype": "body"},
        {"family": "card_grid", "archetype": "body"},
    ])

    assert report["status"] == "fail"
    assert report["issues"][0] == {
        "code": "COMPONENT_FAMILY_CONSECUTIVE_LIMIT",
        "family": "card_grid",
        "first_page_index": 1,
        "last_page_index": 3,
    }


def test_diversity_rejects_generic_cards_over_body_share_floor() -> None:
    report = evaluate_family_diversity([
        {"family": "card_grid", "archetype": "body"},
        {"family": "timeline", "archetype": "body"},
        {"family": "card_grid", "archetype": "body"},
        {"family": "pyramid", "archetype": "body"},
    ])

    assert report["status"] == "fail"
    assert report["generic_family_ratio"] == 0.5
    assert report["issues"][0]["code"] == "GENERIC_COMPONENT_FAMILY_OVERUSED"


def test_diversity_counts_a_composite_slide_once() -> None:
    report = evaluate_family_diversity([
        {
            "families": ["kpi_chart_row", "impact_bar", "fixed_native_group"],
            "archetype": "body",
        },
        {"families": ["card_grid"], "archetype": "body"},
        {"families": ["timeline"], "archetype": "body"},
    ])

    assert report["status"] == "pass"
    assert report["body_page_count"] == 3
    assert report["generic_family_ratio"] == 0.3333

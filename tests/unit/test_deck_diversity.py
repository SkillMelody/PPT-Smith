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

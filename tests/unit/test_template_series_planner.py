from engine.template_series_planner import evaluate_template_series


def _page(index: int, *, purpose: str = "comparison", hero: str = "bar") -> dict:
    return {
        "slide_id": f"S{index:02d}",
        "series_context": {
            "group_id": "countries",
            "purpose": purpose,
            "position": index,
            "total": 5,
            "narrative_tier": "main",
            "hero_visual_type": hero,
            "comparison_anchor": "regional-baseline",
            "shared_scale": True,
        },
    }


def test_comparison_series_keeps_a_shared_anchor_and_allows_comparable_grid() -> None:
    report = evaluate_template_series([_page(index) for index in range(1, 6)])

    assert report["status"] == "pass"
    assert report["series"][0]["recommendation"] == "retain comparable grid"


def test_long_main_series_must_consolidate_or_move_to_appendix() -> None:
    pages = [_page(index) for index in range(1, 7)]
    for page in pages:
        page["series_context"]["total"] = 6

    report = evaluate_template_series(pages)

    assert "TEMPLATE_SERIES_MAIN_NARRATIVE_TOO_LONG" in {
        issue["code"] for issue in report["issues"]
    }


def test_noncomparison_series_cannot_repeat_one_hero_visual_three_times() -> None:
    pages = [_page(index, purpose="sequence") for index in range(1, 4)]
    for page in pages:
        page["series_context"].pop("comparison_anchor")
        page["series_context"].pop("shared_scale")
        page["series_context"]["total"] = 3

    report = evaluate_template_series(pages)

    assert "TEMPLATE_SERIES_HERO_REPETITION" in {
        issue["code"] for issue in report["issues"]
    }

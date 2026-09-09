from __future__ import annotations

from engine.template_page_recipes import evaluate_template_page_recipe


def _contract(archetype: str | None = "case_study") -> dict:
    value = {
        "content_modules": [
            {"role": "context", "information_unit_count": 1},
            {"role": "primary_evidence", "information_unit_count": 3},
            {"role": "implication", "information_unit_count": 2},
        ],
    }
    if archetype is not None:
        value["composition_archetype"] = archetype
    return value


def test_recipe_contract_accepts_complete_case_study() -> None:
    contract = _contract()
    contract["content_modules"][0]["information_unit_count"] = 1

    report = evaluate_template_page_recipe(
        contract,
        slide_id="s1",
        require_declaration=True,
        is_quantitative=False,
    )

    assert report["status"] == "pass"
    assert report["information_unit_count"] == 6


def test_recipe_contract_requires_archetype_for_new_plan_schema() -> None:
    report = evaluate_template_page_recipe(
        _contract(None),
        slide_id="s2",
        require_declaration=True,
        is_quantitative=False,
    )

    assert report["status"] == "fail"
    assert report["issues"][0]["code"] == "TEMPLATE_PAGE_ARCHETYPE_REQUIRED"


def test_data_recipe_requires_native_quantitative_content() -> None:
    contract = _contract("data_evidence")
    contract["content_modules"][0]["role"] = "interpretation"

    report = evaluate_template_page_recipe(
        contract,
        slide_id="s3",
        require_declaration=True,
        is_quantitative=False,
    )

    codes = {issue["code"] for issue in report["issues"]}
    assert "TEMPLATE_PAGE_ARCHETYPE_DATA_REQUIRED" in codes

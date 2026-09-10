from __future__ import annotations

from engine.production_request import resolve_page_budget, validate_production_request


def _assessment(*, minimum: int = 18, recommended: int = 26, maximum: int = 34) -> dict:
    return {
        "minimum_viable_pages": minimum,
        "recommended_pages": recommended,
        "maximum_useful_pages": maximum,
        "basis": ["12 mandatory claims", "8 evidence clusters", "4 chapter transitions"],
    }


def _request(page_contract: dict, *, template: dict | None = None) -> dict:
    request = {
        "schema_version": "1.0.0",
        "request_id": "wef-management-brief",
        "route": "bespoke",
        "page_contract": page_contract,
    }
    if template is not None:
        request["template"] = template
    return request


def test_auto_page_budget_uses_content_recommendation_without_fixed_limit() -> None:
    request = _request({"mode": "auto", "overflow_policy": "ask", "underflow_policy": "fewer_pages"})

    assert validate_production_request(request) == []
    result = resolve_page_budget(request["page_contract"], _assessment())

    assert result["status"] == "accepted"
    assert result["planned_pages"] == 26
    assert result["hard_min"] == 18
    assert result["hard_max"] == 34
    assert result["reason"] == "content_recommendation"


def test_exact_page_budget_rejects_content_overflow_instead_of_cramming() -> None:
    contract = {
        "mode": "exact", "exact_pages": 15,
        "overflow_policy": "ask", "underflow_policy": "fewer_pages",
    }

    result = resolve_page_budget(contract, _assessment(minimum=18))

    assert result["status"] == "conflict"
    assert result["code"] == "PAGE_CONTRACT_CONTENT_OVERFLOW"
    assert result["planned_pages"] is None
    assert result["alternatives"] == ["increase_pages", "appendix", "split_deck", "reduce_scope"]


def test_exact_page_budget_rejects_underflow_instead_of_inventing_content() -> None:
    contract = {
        "mode": "exact", "exact_pages": 40,
        "overflow_policy": "ask", "underflow_policy": "ask",
    }

    result = resolve_page_budget(contract, _assessment(maximum=30))

    assert result["status"] == "conflict"
    assert result["code"] == "PAGE_CONTRACT_CONTENT_UNDERFLOW"
    assert "invent_content" not in result["alternatives"]
    assert result["alternatives"] == ["fewer_pages", "request_more_source_material"]


def test_range_page_budget_selects_recommendation_inside_user_bounds() -> None:
    contract = {
        "mode": "range", "min_pages": 20, "max_pages": 30,
        "overflow_policy": "appendix", "underflow_policy": "fewer_pages",
    }

    result = resolve_page_budget(contract, _assessment(recommended=26))

    assert result["status"] == "accepted"
    assert result["planned_pages"] == 26
    assert result["hard_min"] == 20
    assert result["hard_max"] == 30
    assert result["reason"] == "content_recommendation_within_user_range"


def test_target_page_budget_is_preference_not_silent_hard_constraint() -> None:
    contract = {
        "mode": "target", "target_pages": 15, "tolerance_pages": 2,
        "overflow_policy": "ask", "underflow_policy": "fewer_pages",
    }

    result = resolve_page_budget(contract, _assessment(minimum=18, recommended=26))

    assert result["status"] == "accepted_with_adjustment"
    assert result["planned_pages"] == 18
    assert result["code"] == "PAGE_TARGET_BELOW_CONTENT_MINIMUM"
    assert result["requested_pages"] == 15


def test_page_contract_schema_rejects_wrong_mode_fields() -> None:
    request = _request({
        "mode": "exact", "target_pages": 20,
        "overflow_policy": "ask", "underflow_policy": "fewer_pages",
    })

    findings = validate_production_request(request)

    assert any(item["code"] == "SCHEMA" for item in findings)


def test_uploaded_template_is_first_class_request_input() -> None:
    request = _request(
        {"mode": "auto", "overflow_policy": "ask", "underflow_policy": "fewer_pages"},
        template={
            "use_mode": "style_transfer",
            "source_sha256": "sha256:" + "a" * 64,
            "required": True,
        },
    )

    assert validate_production_request(request) == []


def test_v4_declares_three_independent_production_routes() -> None:
    contract = {"mode": "auto", "overflow_policy": "ask", "underflow_policy": "fewer_pages"}

    for route in ("standard", "bespoke", "template"):
        request = _request(contract)
        request["route"] = route
        assert validate_production_request(request) == []

    invalid = _request(contract)
    invalid["route"] = "bespoke-template"
    assert any(item["code"] == "SCHEMA" for item in validate_production_request(invalid))

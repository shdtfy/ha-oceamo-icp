"""Regression tests for Reef ICP 0.15.0 supply-system additions."""

from __future__ import annotations

import pytest

from custom_components.reef_icp.const import (
    SUPPLY_SYSTEM_AQUAFOREST_COMPONENT_123,
    SUPPLY_SYSTEM_KORALLEN_ZUCHT_CORAL_SYSTEM,
    SUPPLY_SYSTEM_RED_SEA_REEF_CARE_7_PART,
    SUPPLY_SYSTEM_REEF_MOONSHINERS,
    SUPPLY_SYSTEM_REEF_ZLEMENTS,
    SUPPLY_SYSTEM_SANGOKAI_BALANCE,
    SUPPLY_SYSTEM_TROPIC_MARIN_ALL_FOR_REEF,
)
from custom_components.reef_icp.recommendations import build_supply_recommendations


def measurement(key: str, value: float, unit: str, target_min: float, target_max: float, *, category: str = "trace_elements", severity: str = "warning", direction: str = "low") -> dict:
    return {"key": key, "name": key, "category": category, "value": value, "raw_value": str(value), "unit": unit, "target": {"type": "range", "min": target_min, "max": target_max}, "status": {"severity": severity, "direction": direction}}


def test_all_for_reef_scales_published_maintenance_doses() -> None:
    result = build_supply_recommendations(SUPPLY_SYSTEM_TROPIC_MARIN_ALL_FOR_REEF, 250, [])
    guidance = result["maintenance_guidance"]
    assert guidance["start_daily_ml"] == pytest.approx(12.5)
    assert guidance["weekly_increase_ml"] == pytest.approx(6.25)
    assert guidance["max_daily_ml"] == pytest.approx(62.5)
    assert result["items"] == []


def test_aquaforest_component_123_keeps_equal_maintenance_dosing() -> None:
    result = build_supply_recommendations(SUPPLY_SYSTEM_AQUAFOREST_COMPONENT_123, 200, [])
    guidance = result["maintenance_guidance"]
    assert guidance["typical_daily_ml_each"] == pytest.approx(50.0)
    assert guidance["equal_amounts"] is True
    assert result["numeric_trace_calculation"] is False


def test_red_sea_is_guidance_only_to_avoid_cross_generation_formula() -> None:
    result = build_supply_recommendations(SUPPLY_SYSTEM_RED_SEA_REEF_CARE_7_PART, 300, [measurement("calcium", 390, "mg/l", 420, 440)])
    assert result["mode"] == "official_guidance"
    assert result["items"] == []
    assert result["maintenance_guidance"]["use_manufacturer_recipe"] is True


@pytest.mark.parametrize(("key", "value", "unit", "target_min", "expected_product", "expected_dose"), [
    ("calcium", 410, "mg/l", 420, "SANGOKAI BALANCE Ca-1", 25.0),
    ("alkalinitaet", 7.0, "dKH", 8.0, "SANGOKAI BALANCE KH", 40.0),
    ("kalium", 380, "mg/l", 400, "SANGOKAI INDIVIDUAL K", 20.0),
    ("strontium", 6, "mg/l", 8, "SANGOKAI INDIVIDUAL Sr", 20.0),
    ("bor", 4.0, "mg/l", 4.5, "SANGOKAI INDIVIDUAL B", 10.0),
    ("bromid", 60, "mg/l", 65, "SANGOKAI INDIVIDUAL BrF", 10.0),
    ("iod", 15, "µg/l", 65, "SANGOKAI INDIVIDUAL IF", 1.0),
])
def test_sangokai_verified_numeric_rules(key: str, value: float, unit: str, target_min: float, expected_product: str, expected_dose: float) -> None:
    result = build_supply_recommendations(SUPPLY_SYSTEM_SANGOKAI_BALANCE, 100, [measurement(key, value, unit, target_min, target_min + 10)])
    assert len(result["items"]) == 1
    item = result["items"][0]
    assert item["product"] == expected_product
    assert item["dose_amount"] == pytest.approx(expected_dose)


def test_sangokai_calcium_carries_ca2_balance_note() -> None:
    result = build_supply_recommendations(SUPPLY_SYSTEM_SANGOKAI_BALANCE, 100, [measurement("calcium", 410, "mg/l", 420, 440)])
    item = result["items"][0]
    assert item["companion_product"] == "SANGOKAI BALANCE Ca-2"
    assert item["companion_dose_equal_to_primary"] is True


def test_kz_coral_system_scales_weekly_maintenance() -> None:
    result = build_supply_recommendations(SUPPLY_SYSTEM_KORALLEN_ZUCHT_CORAL_SYSTEM, 300, [])
    guidance = result["maintenance_guidance"]
    assert guidance["weekly_ml_each"] == pytest.approx(15.0)
    assert len(guidance["products"]) == 4


@pytest.mark.parametrize("system", [SUPPLY_SYSTEM_REEF_ZLEMENTS, SUPPLY_SYSTEM_REEF_MOONSHINERS])
def test_external_tool_systems_do_not_invent_numeric_trace_formula(system: str) -> None:
    result = build_supply_recommendations(system, 100, [measurement("iod", 40, "µg/l", 60, 80)])
    assert result["mode"] == "official_calculator"
    assert result["items"][0]["action"] == "official_calculator"
    assert "dose_amount" not in result["items"][0]


def test_new_supply_systems_still_ignore_osmosis_measurements() -> None:
    osmosis = measurement("calcium", 1, "mg/l", 420, 440, category="osmosis", severity="critical", direction="low")
    for system in (SUPPLY_SYSTEM_SANGOKAI_BALANCE, SUPPLY_SYSTEM_REEF_ZLEMENTS, SUPPLY_SYSTEM_REEF_MOONSHINERS):
        result = build_supply_recommendations(system, 100, [osmosis])
        assert result is not None
        assert result["items"] == []

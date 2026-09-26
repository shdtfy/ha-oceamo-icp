"""Regression tests for supply-system recommendation calculations."""

from __future__ import annotations

import pytest

from custom_components.reef_icp.const import (
    SUPPLY_SYSTEM_ATI_ESSENTIALS_PRO,
    SUPPLY_SYSTEM_FAUNA_MARIN_BALLING_LIGHT,
    SUPPLY_SYSTEM_OCEAMO_DUO,
    SUPPLY_SYSTEM_TRITON_METHOD,
    SUPPLY_SYSTEM_TROPIC_MARIN_ORIGINAL_BALLING,
)
from custom_components.reef_icp.recommendations import build_supply_recommendations


def measurement(
    key: str,
    value: float,
    unit: str,
    target_min: float,
    target_max: float,
    *,
    category: str = "trace_elements",
    severity: str = "warning",
    direction: str = "low",
    custom_target: tuple[float, float] | None = None,
) -> dict:
    item = {
        "key": key,
        "name": key,
        "category": category,
        "value": value,
        "raw_value": str(value),
        "unit": unit,
        "target": {"type": "range", "min": target_min, "max": target_max},
        "status": {"severity": severity, "direction": direction},
    }
    if custom_target is not None:
        item["custom_target"] = {
            "type": "range",
            "min": custom_target[0],
            "max": custom_target[1],
        }
    return item


def first_item(result: dict) -> dict:
    assert result["supported"] is True
    assert len(result["items"]) == 1
    return result["items"][0]


def test_fauna_marin_iodine_numeric_rule() -> None:
    result = build_supply_recommendations(
        SUPPLY_SYSTEM_FAUNA_MARIN_BALLING_LIGHT,
        100,
        [measurement("iod", 50, "µg/l", 60, 80)],
    )
    item = first_item(result)
    assert item["product"] == "Fauna Marin Elementals Trace I"
    assert item["dose_amount"] == pytest.approx(1.0)


def test_ati_iodine_numeric_rule() -> None:
    result = build_supply_recommendations(
        SUPPLY_SYSTEM_ATI_ESSENTIALS_PRO,
        100,
        [measurement("iod", 50, "µg/l", 60, 80)],
    )
    item = first_item(result)
    assert item["product"] == "ATI ICP Element Jod"
    assert item["dose_amount"] == pytest.approx(1.0)


def test_oceamo_iodine_numeric_rule() -> None:
    result = build_supply_recommendations(
        SUPPLY_SYSTEM_OCEAMO_DUO,
        100,
        [measurement("iod", 50, "µg/l", 60, 80)],
    )
    item = first_item(result)
    assert item["product"] == "Oceamo Single Elements Iod"
    assert item["dose_amount"] == pytest.approx(0.2)


def test_triton_uses_official_calculator_for_low_trace_element() -> None:
    result = build_supply_recommendations(
        SUPPLY_SYSTEM_TRITON_METHOD,
        100,
        [measurement("iod", 50, "µg/l", 60, 80)],
    )
    item = first_item(result)
    assert item["action"] == "official_calculator"
    assert "triton" in item["source_url"].lower()


@pytest.mark.parametrize(
    ("key", "value", "unit", "target_min", "product", "expected_dose"),
    [
        ("calcium", 400, "mg/l", 420, "Tropic Marin Original Balling", 100.0),
        ("alkalinitaet", 7.0, "dKH", 8.4, "Tropic Marin Original Balling", 50.0),
        ("magnesium", 1275, "mg/l", 1300, "Tropic Marin Bio-Magnesium Liquid", 50.0),
        ("kalium", 390, "mg/l", 400, "Tropic Marin Potassium", 10.0),
        ("iod", 45, "µg/l", 60, "Tropic Marin Iodine", 1.5),
        ("bromid", 55, "mg/l", 60, "Tropic Marin Bromine", 5.0),
        ("eisen", 0.0, "µg/l", 1.0, "Tropic Marin Iron", 1.0),
    ],
)
def test_tropic_marin_verified_correction_rules(
    key: str,
    value: float,
    unit: str,
    target_min: float,
    product: str,
    expected_dose: float,
) -> None:
    result = build_supply_recommendations(
        SUPPLY_SYSTEM_TROPIC_MARIN_ORIGINAL_BALLING,
        100,
        [measurement(key, value, unit, target_min, target_min + 10)],
    )
    item = first_item(result)
    assert item["product"] == product
    assert item["dose_amount"] == pytest.approx(expected_dose)


def test_tropic_marin_exposes_trace_maintenance_without_inventing_mix_strengths() -> None:
    result = build_supply_recommendations(
        SUPPLY_SYSTEM_TROPIC_MARIN_ORIGINAL_BALLING,
        200,
        [],
    )
    assert result["trace_elements_implemented"] is True
    assert result["numeric_trace_calculation"] is True
    assert result["trace_maintenance"]["k_plus_elements"]["daily_dose_ml_per_100_l"] == 1.0
    assert result["trace_maintenance"]["a_minus_elements"]["max_daily_dose_ml_per_100_l"] == 2.0


def test_osmosis_measurements_never_generate_aquarium_dosing() -> None:
    osmosis_calcium = measurement(
        "calcium",
        1.0,
        "mg/l",
        400,
        440,
        category="osmosis",
        severity="critical",
        direction="low",
    )

    for system in (
        SUPPLY_SYSTEM_FAUNA_MARIN_BALLING_LIGHT,
        SUPPLY_SYSTEM_ATI_ESSENTIALS_PRO,
        SUPPLY_SYSTEM_OCEAMO_DUO,
        SUPPLY_SYSTEM_TRITON_METHOD,
        SUPPLY_SYSTEM_TROPIC_MARIN_ORIGINAL_BALLING,
    ):
        result = build_supply_recommendations(system, 100, [osmosis_calcium])
        assert result is not None
        assert result["items"] == []


def test_personal_target_changes_calculation_but_not_input_measurement() -> None:
    source = measurement(
        "calcium",
        410,
        "mg/l",
        400,
        440,
        severity="ok",
        direction=None,
        custom_target=(420, 440),
    )
    original_status = dict(source["status"])
    original_target = dict(source["target"])

    result = build_supply_recommendations(
        SUPPLY_SYSTEM_TROPIC_MARIN_ORIGINAL_BALLING,
        100,
        [source],
    )
    item = first_item(result)
    assert item["target_source"] == "aquarium_custom"
    assert item["dose_amount"] == pytest.approx(50.0)
    assert source["status"] == original_status
    assert source["target"] == original_target

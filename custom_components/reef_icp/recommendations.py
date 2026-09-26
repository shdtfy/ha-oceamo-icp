"""Recommendation wrapper adding aquarium-specific personal target ranges.

The established manufacturer calculation rules stay in ``recommendations_core``.
This wrapper only substitutes a user's optional aquarium target range while
building Reef ICP supply-system recommendations. Laboratory targets and status
stored in the imported ICP report remain untouched.
"""

from __future__ import annotations

import copy
from typing import Any

from .const import (
    SUPPLY_SYSTEM_NAMES,
    SUPPLY_SYSTEM_TROPIC_MARIN_ORIGINAL_BALLING,
)
from .recommendations_core import *  # noqa: F403
from .recommendations_core import (
    _generic_correction,
    build_supply_recommendations as _build_supply_recommendations_core,
)


_TROPIC_MARIN_ORIGINAL_BALLING_URL = (
    "https://www.tropic-marin-smartinfo.com/original-balling-components"
)

# Manufacturer reference for prepared Original Balling solutions:
# 50 ml per 100 l raises calcium by 10 mg/l (Part A) and alkalinity by
# 1.4 dKH (Part B). The published maximum is 150 ml of each solution per
# 100 l/day, corresponding to +30 mg/l Ca or +4.2 dKH per day.
_TROPIC_MARIN_ORIGINAL_BALLING_RULES: dict[str, dict[str, Any]] = {
    "calcium": {
        "name": "Calcium",
        "product": "Tropic Marin Original Balling",
        "kind": "core",
        "dose_amount": 50.0,
        "dose_unit": "ml",
        "increase": 10.0,
        "unit": "mg/l",
        "max_daily_increase": 30.0,
        "solution": "Part A",
        "requires_report_type": None,
        "source_name": "Tropic Marin Original Balling",
        "source_url": _TROPIC_MARIN_ORIGINAL_BALLING_URL,
    },
    "alkalinitaet": {
        "name": "Alkalinität",
        "product": "Tropic Marin Original Balling",
        "kind": "core",
        "dose_amount": 50.0,
        "dose_unit": "ml",
        "increase": 1.4,
        "unit": "dKH",
        "max_daily_increase": 4.2,
        "solution": "Part B",
        "requires_report_type": None,
        "source_name": "Tropic Marin Original Balling",
        "source_url": _TROPIC_MARIN_ORIGINAL_BALLING_URL,
    },
}


def _build_tropic_marin_original_balling(
    aquarium_volume_l: Any,
    measurements: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build numeric Original Balling A/B corrections from manufacturer data."""
    system = SUPPLY_SYSTEM_TROPIC_MARIN_ORIGINAL_BALLING
    system_name = SUPPLY_SYSTEM_NAMES[system]

    try:
        volume_l = float(aquarium_volume_l)
    except (TypeError, ValueError):
        volume_l = 0.0

    if volume_l <= 0:
        return {
            "system": system,
            "system_name": system_name,
            "supported": False,
            "reason": "missing_volume",
            "items": [],
        }

    items: list[dict[str, Any]] = []
    for measurement in measurements:
        rule = _TROPIC_MARIN_ORIGINAL_BALLING_RULES.get(
            str(measurement.get("key") or "")
        )
        if rule is None:
            continue
        item = _generic_correction(measurement, volume_l, rule)
        if item is not None:
            items.append(item)

    return {
        "system": system,
        "system_name": system_name,
        "supported": True,
        "volume_l": volume_l,
        "mode": "calculated",
        "items": items,
        "calculated_keys": sorted(_TROPIC_MARIN_ORIGINAL_BALLING_RULES),
        "maintenance_note": "tropic_marin_original_balling_consumption",
        "maintenance_requires_consumption": True,
        "maintenance_source_url": _TROPIC_MARIN_ORIGINAL_BALLING_URL,
        "trace_elements_implemented": False,
        "numeric_trace_calculation": False,
    }


def _measurement_for_personal_target(
    measurement: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    """Return a calculation copy using the aquarium target when configured."""
    target = measurement.get("custom_target")
    if not isinstance(target, dict) or target.get("type") != "range":
        return measurement, False

    minimum = target.get("min")
    maximum = target.get("max")
    if not isinstance(minimum, (int, float)) or not isinstance(
        maximum, (int, float)
    ):
        return measurement, False

    prepared = copy.deepcopy(measurement)
    prepared["target"] = {
        "type": "range",
        "min": float(minimum),
        "max": float(maximum),
    }

    current = prepared.get("value")
    if not isinstance(current, (int, float)) or isinstance(current, bool):
        prepared["status"] = {
            "severity": "unknown",
            "direction": None,
        }
    elif float(current) < float(minimum):
        prepared["status"] = {
            "severity": "warning",
            "direction": "low",
        }
    elif float(current) > float(maximum):
        prepared["status"] = {
            "severity": "warning",
            "direction": "high",
        }
    else:
        prepared["status"] = {
            "severity": "ok",
            "direction": None,
        }

    prepared["reef_target_source"] = "aquarium_custom"
    return prepared, True


def build_supply_recommendations(
    supply_system: str | None,
    aquarium_volume_l: Any,
    measurements: list[dict[str, Any]],
    report_type: str | None = None,
) -> dict[str, Any] | None:
    """Build supply recommendations using personal targets where configured."""
    prepared_measurements: list[dict[str, Any]] = []
    custom_keys: set[str] = set()

    for measurement in measurements:
        prepared, used_custom_target = _measurement_for_personal_target(
            measurement
        )
        prepared_measurements.append(prepared)
        if used_custom_target:
            custom_keys.add(str(measurement.get("key") or ""))

    if supply_system == SUPPLY_SYSTEM_TROPIC_MARIN_ORIGINAL_BALLING:
        result = _build_tropic_marin_original_balling(
            aquarium_volume_l,
            prepared_measurements,
        )
    else:
        result = _build_supply_recommendations_core(
            supply_system,
            aquarium_volume_l,
            prepared_measurements,
            report_type,
        )
    if result is None:
        return None

    result = copy.deepcopy(result)
    result["custom_target_keys"] = sorted(key for key in custom_keys if key)

    for item in result.get("items", []):
        if not isinstance(item, dict):
            continue
        item["target_source"] = (
            "aquarium_custom"
            if str(item.get("key") or "") in custom_keys
            else "laboratory"
        )

    return result

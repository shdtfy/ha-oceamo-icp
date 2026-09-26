"""Recommendation wrapper adding aquarium-specific personal target ranges.

The established manufacturer calculation rules stay in ``recommendations_core``.
This wrapper substitutes optional aquarium target ranges, adds the independently
verified Tropic Marin correction products, and keeps RO/osmosis measurements out
of aquarium dosing recommendations.
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
_TROPIC_MARIN_POTASSIUM_URL = (
    "https://www.tropic-marin-smartinfo.com/potassium"
)
_TROPIC_MARIN_BIO_MAGNESIUM_URL = (
    "https://www.tropic-marin-smartinfo.com/bio-magnesium"
)
_TROPIC_MARIN_IODINE_URL = (
    "https://www.tropic-marin-smartinfo.com/iodine"
)
_TROPIC_MARIN_BROMINE_URL = (
    "https://www.tropic-marin-smartinfo.com/bromine"
)
_TROPIC_MARIN_IRON_URL = (
    "https://www.tropic-marin-smartinfo.com/iron"
)
_TROPIC_MARIN_K_ELEMENTS_URL = (
    "https://www.tropic-marin-smartinfo.com/k-elements"
)
_TROPIC_MARIN_A_ELEMENTS_URL = (
    "https://www.tropic-marin-smartinfo.com/a-elements"
)

# Manufacturer references used below:
# - Original Balling: 50 ml / 100 l -> +10 mg/l Ca or +1.4 dKH,
#   maximum 150 ml / 100 l / day.
# - Potassium: 10 ml / 100 l -> +10 mg/l K,
#   maximum +20 mg/l / day.
# - Bio-Magnesium Liquid: 50 ml / 100 l -> +25 mg/l Mg,
#   maximum +25 mg/l / day.
# - Iodine: 1.5 ml / 100 l -> +15 µg/l I,
#   maximum +30 µg/l / day.
# - Bromine: 5 ml / 100 l -> +5 mg/l Br,
#   maximum +10 mg/l / day.
# - Iron: 1 ml / 100 l -> +1 µg/l Fe,
#   maximum +4 µg/l / day.
#
# K+ Elements and A- Elements are intentionally NOT converted into
# analyte-specific correction formulas: Tropic Marin publishes a maintenance
# dosage for the mixed solutions, but not the individual concentration of each
# element in those mixtures.
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
    "magnesium": {
        "name": "Magnesium",
        "product": "Tropic Marin Bio-Magnesium Liquid",
        "kind": "core_correction",
        "dose_amount": 50.0,
        "dose_unit": "ml",
        "increase": 25.0,
        "unit": "mg/l",
        "max_daily_increase": 25.0,
        "solution": None,
        "requires_report_type": None,
        "source_name": "Tropic Marin Bio-Magnesium",
        "source_url": _TROPIC_MARIN_BIO_MAGNESIUM_URL,
    },
    "kalium": {
        "name": "Kalium",
        "product": "Tropic Marin Potassium",
        "kind": "single_element",
        "dose_amount": 10.0,
        "dose_unit": "ml",
        "increase": 10.0,
        "unit": "mg/l",
        "max_daily_increase": 20.0,
        "solution": None,
        "requires_report_type": None,
        "source_name": "Tropic Marin Potassium",
        "source_url": _TROPIC_MARIN_POTASSIUM_URL,
    },
    "iod": {
        "name": "Iod",
        "product": "Tropic Marin Iodine",
        "kind": "single_element",
        "dose_amount": 1.5,
        "dose_unit": "ml",
        "increase": 15.0,
        "unit": "µg/l",
        "max_daily_increase": 30.0,
        "solution": None,
        "requires_report_type": None,
        "source_name": "Tropic Marin Iodine",
        "source_url": _TROPIC_MARIN_IODINE_URL,
    },
    "bromid": {
        "name": "Bromid",
        "product": "Tropic Marin Bromine",
        "kind": "single_element",
        "dose_amount": 5.0,
        "dose_unit": "ml",
        "increase": 5.0,
        "unit": "mg/l",
        "max_daily_increase": 10.0,
        "solution": None,
        "requires_report_type": None,
        "source_name": "Tropic Marin Bromine",
        "source_url": _TROPIC_MARIN_BROMINE_URL,
    },
    "eisen": {
        "name": "Eisen",
        "product": "Tropic Marin Iron",
        "kind": "single_element",
        "dose_amount": 1.0,
        "dose_unit": "ml",
        "increase": 1.0,
        "unit": "µg/l",
        "max_daily_increase": 4.0,
        "solution": None,
        "requires_report_type": None,
        "source_name": "Tropic Marin Iron",
        "source_url": _TROPIC_MARIN_IRON_URL,
    },
}

_TROPIC_MARIN_TRACE_MAINTENANCE = {
    "k_plus_elements": {
        "product": "Tropic Marin K+ Elements",
        "elements": [
            "barium",
            "bor",
            "chrom",
            "eisen",
            "cobalt",
            "kupfer",
            "mangan",
            "nickel",
            "strontium",
            "zink",
        ],
        "daily_dose_ml_per_100_l": 1.0,
        "max_daily_dose_ml_per_100_l": 2.0,
        "source_url": _TROPIC_MARIN_K_ELEMENTS_URL,
    },
    "a_minus_elements": {
        "product": "Tropic Marin A- Elements",
        "elements": [
            "bromid",
            "fluorid",
            "iod",
            "lithium",
            "molybdaen",
            "selen",
            "vanadium",
        ],
        "daily_dose_ml_per_100_l": 1.0,
        "max_daily_dose_ml_per_100_l": 2.0,
        "source_url": _TROPIC_MARIN_A_ELEMENTS_URL,
    },
}


def _is_aquarium_measurement(measurement: dict[str, Any]) -> bool:
    """Return True only for aquarium-water values used for dosing guidance."""
    return str(measurement.get("category") or "") != "osmosis"


def _build_tropic_marin_original_balling(
    aquarium_volume_l: Any,
    measurements: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build verified Tropic Marin corrections from published product strengths."""
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
        if not _is_aquarium_measurement(measurement):
            continue
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
        "trace_elements_implemented": True,
        "numeric_trace_calculation": True,
        "trace_maintenance": copy.deepcopy(_TROPIC_MARIN_TRACE_MAINTENANCE),
        "trace_maintenance_note": (
            "K+ Elements and A- Elements are mixed maintenance supplements. "
            "Their published 1 ml/100 l/day dosage is preserved as guidance; "
            "Reef ICP does not invent individual element concentrations for them."
        ),
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
    """Build supply recommendations using aquarium-water values only."""
    prepared_measurements: list[dict[str, Any]] = []
    custom_keys: set[str] = set()

    for measurement in measurements:
        # RO/osmosis measurements belong to source-water diagnostics and must
        # never generate aquarium supplement dosing instructions.
        if not _is_aquarium_measurement(measurement):
            continue

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

"""Recommendation wrapper adding aquarium-specific personal target ranges.

The established manufacturer calculation rules stay in ``recommendations_core``.
This wrapper only substitutes a user's optional aquarium target range while
building Reef ICP supply-system recommendations. Laboratory targets and status
stored in the imported ICP report remain untouched.
"""

from __future__ import annotations

import copy
from typing import Any

from .recommendations_core import *  # noqa: F403
from .recommendations_core import (
    build_supply_recommendations as _build_supply_recommendations_core,
)


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

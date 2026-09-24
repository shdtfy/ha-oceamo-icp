"""Provider-independent supply-system recommendations for Reef ICP."""

from __future__ import annotations

from typing import Any

from .const import (
    SUPPLY_SYSTEM_FAUNA_MARIN_BALLING_LIGHT,
    SUPPLY_SYSTEM_NAMES,
)


# Standard Fauna Marin Balling Light working-solution strengths:
# 10 ml / 100 l raises KH by 0.5 dKH, Ca by 11 mg/l, Mg by 5 mg/l.
_BALLING_LIGHT_COMPONENTS: dict[str, dict[str, Any]] = {
    "calcium": {
        "name": "Calcium",
        "product": "Fauna Marin Balling Light Calcium Mix",
        "solution": "Kanister 1",
        "increase_per_10ml_100l": 11.0,
    },
    "magnesium": {
        "name": "Magnesium",
        "product": "Fauna Marin Balling Light Magnesium Mix",
        "solution": "Kanister 2",
        "increase_per_10ml_100l": 5.0,
    },
    "alkalinitaet": {
        "name": "Alkalinität",
        "product": "Fauna Marin Balling Light Carbonate Mix",
        "solution": "Kanister 3",
        "increase_per_10ml_100l": 0.5,
    },
}


def _target_relation(
    measurement: dict[str, Any],
) -> tuple[str | None, float | None]:
    """Return low/high relation and the nearest target boundary."""
    current = measurement.get("value")
    target = measurement.get("target")

    if not isinstance(current, (int, float)) or not isinstance(target, dict):
        return None, None

    target_type = target.get("type")

    if target_type == "exact":
        desired = target.get("value")
        if not isinstance(desired, (int, float)):
            return None, None
        if current < desired:
            return "low", float(desired)
        if current > desired:
            return "high", float(desired)
        return "ok", float(desired)

    if target_type == "range":
        minimum = target.get("min")
        maximum = target.get("max")
        if not isinstance(minimum, (int, float)) or not isinstance(
            maximum, (int, float)
        ):
            return None, None
        if current < minimum:
            return "low", float(minimum)
        if current > maximum:
            return "high", float(maximum)
        return "ok", float(current)

    if target_type == "lower_limit":
        minimum = target.get("min")
        if not isinstance(minimum, (int, float)):
            return None, None
        if current < minimum:
            return "low", float(minimum)
        return "ok", float(current)

    if target_type == "upper_limit":
        maximum = target.get("max")
        if not isinstance(maximum, (int, float)):
            return None, None
        if current > maximum:
            return "high", float(maximum)
        return "ok", float(current)

    return None, None


def _balling_light_correction(
    measurement: dict[str, Any],
    volume_l: float,
) -> dict[str, Any] | None:
    """Calculate one Balling Light correction from a normalized ICP value."""
    key = str(measurement.get("key", ""))
    component = _BALLING_LIGHT_COMPONENTS.get(key)
    if component is None:
        return None

    current = measurement.get("value")
    if not isinstance(current, (int, float)):
        return None

    status = measurement.get("status") or {}
    severity = str(status.get("severity", "unknown"))
    if severity not in {"warning", "critical"}:
        return None

    relation, target_value = _target_relation(measurement)
    if relation not in {"low", "high"} or target_value is None:
        return None

    common = {
        "key": key,
        "name": component["name"],
        "product": component["product"],
        "solution": component["solution"],
        "current": float(current),
        "target": float(target_value),
        "unit": measurement.get("unit"),
        "severity": severity,
    }

    if relation == "high":
        return {
            **common,
            "action": "reduce_or_pause",
            "dose_ml": 0.0,
        }

    delta = float(target_value) - float(current)
    if delta <= 0:
        return None

    # Manufacturer working solution:
    # 10 ml / 100 l raises the parameter by increase_per_10ml_100l.
    dose_ml = (
        delta
        / float(component["increase_per_10ml_100l"])
        * 10.0
        * (volume_l / 100.0)
    )

    return {
        **common,
        "action": "correction_dose",
        "delta": delta,
        "dose_ml": round(dose_ml, 2),
    }


def build_supply_recommendations(
    supply_system: str | None,
    aquarium_volume_l: Any,
    measurements: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Build recommendations from normalized ICP values and aquarium profile."""
    if not supply_system or supply_system == "none":
        return None

    try:
        volume_l = float(aquarium_volume_l)
    except (TypeError, ValueError):
        return {
            "system": supply_system,
            "system_name": SUPPLY_SYSTEM_NAMES.get(
                supply_system, supply_system
            ),
            "supported": False,
            "reason": "missing_volume",
            "items": [],
        }

    if volume_l <= 0:
        return {
            "system": supply_system,
            "system_name": SUPPLY_SYSTEM_NAMES.get(
                supply_system, supply_system
            ),
            "supported": False,
            "reason": "missing_volume",
            "items": [],
        }

    if supply_system != SUPPLY_SYSTEM_FAUNA_MARIN_BALLING_LIGHT:
        return {
            "system": supply_system,
            "system_name": SUPPLY_SYSTEM_NAMES.get(
                supply_system, supply_system
            ),
            "supported": False,
            "reason": "system_not_implemented",
            "volume_l": volume_l,
            "items": [],
        }

    items = [
        item
        for measurement in measurements
        if (item := _balling_light_correction(measurement, volume_l))
        is not None
    ]

    return {
        "system": supply_system,
        "system_name": SUPPLY_SYSTEM_NAMES.get(
            supply_system, supply_system
        ),
        "supported": True,
        "volume_l": volume_l,
        "scope": "balling_light_core",
        "items": items,
        "calculated_keys": ["calcium", "magnesium", "alkalinitaet"],
        "maintenance_requires_consumption": True,
        "trace_elements_implemented": False,
    }

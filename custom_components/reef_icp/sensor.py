"""Sensor platform for Reef ICP."""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any, override

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    CONF_AQUARIUM_VOLUME_L,
    CONF_REPORTS,
    CONF_STOCKING_PROFILE,
    CONF_SUPPLY_SYSTEM,
    DOMAIN,
    STOCKING_PROFILE_FISH_ONLY,
    STOCKING_PROFILE_LPS_DOMINANT,
    STOCKING_PROFILE_MIXED_REEF,
    STOCKING_PROFILE_NAMES,
    STOCKING_PROFILE_OTHER,
    STOCKING_PROFILE_SOFT_CORAL_DOMINANT,
    STOCKING_PROFILE_SPS_DOMINANT,
    SUPPLY_SYSTEM_NAMES,
)
from .recommendations import build_supply_recommendations
from .statistics import statistic_id_for

ANALYSIS_NUMBER_UNIQUE_ID_V1 = "_analysis_number"
ANALYSIS_NUMBER_UNIQUE_ID_V2 = "_analysis_number_v2"


def _reports(entry: ConfigEntry) -> list[dict[str, Any]]:
    """Return all stored reports."""
    return list(entry.options.get(CONF_REPORTS, []))


def _aquarium_profile(entry: ConfigEntry) -> dict[str, Any]:
    """Return persistent aquarium settings used across all ICP providers."""
    volume = entry.options.get(CONF_AQUARIUM_VOLUME_L)
    stocking_profile = entry.options.get(CONF_STOCKING_PROFILE)
    system = entry.options.get(CONF_SUPPLY_SYSTEM)
    return {
        "aquarium_volume_l": volume,
        "stocking_profile": stocking_profile,
        "stocking_profile_name": STOCKING_PROFILE_NAMES.get(
            str(stocking_profile),
            str(stocking_profile),
        )
        if stocking_profile
        else None,
        "supply_system": system,
        "supply_system_name": SUPPLY_SYSTEM_NAMES.get(str(system), str(system))
        if system
        else None,
    }


def _report_sort_key(report: dict[str, Any]) -> str:
    """Return the chronological sort key used by the integration."""
    metadata = report.get("metadata", {})
    return str(
        metadata.get("sample_taken")
        or metadata.get("analysis_date")
        or ""
    )


def _report_provider(report: dict[str, Any] | None) -> str:
    """Return provider ID, treating legacy reports as Oceamo."""
    if report is None:
        return "oceamo"
    return str(
        report.get("provider")
        or report.get("metadata", {}).get("provider")
        or "oceamo"
    )


def _report_provider_name(report: dict[str, Any] | None) -> str:
    """Return a display name for the report provider."""
    if report is None:
        return ""
    provider = _report_provider(report)
    return str(
        report.get("provider_name")
        or report.get("metadata", {}).get("provider_name")
        or ("Oceamo" if provider == "oceamo" else provider)
    )


def _report_type(report: dict[str, Any] | None) -> str | None:
    """Return a report-type hint, including sensible legacy fallbacks."""
    if report is None:
        return None
    value = report.get("report_type") or report.get("metadata", {}).get("report_type")
    if value:
        return str(value)
    provider = _report_provider(report)
    if provider == "oceamo":
        return "classic_icp"
    if provider == "fauna_marin":
        return "reef_icp"
    if provider == "ati":
        return "ati_icp"
    return None


def _report_identity(report: dict[str, Any]) -> tuple[str, str]:
    """Return a provider-specific identity for one stored report."""
    metadata = report.get("metadata", {})
    report_id = str(
        metadata.get("provider_report_id")
        or metadata.get("analysis_number")
        or ""
    )
    return (_report_provider(report), report_id)


def _latest_report(entry: ConfigEntry) -> dict[str, Any]:
    """Return the newest stored report."""
    reports = _reports(entry)
    return max(reports, key=_report_sort_key)


def _previous_report(
    entry: ConfigEntry, latest_report: dict[str, Any]
) -> dict[str, Any] | None:
    """Return the report immediately before the latest one."""
    latest_identity = _report_identity(latest_report)
    reports = sorted(_reports(entry), key=_report_sort_key)

    older_reports = [
        report
        for report in reports
        if _report_identity(report) != latest_identity
        and _report_sort_key(report) <= _report_sort_key(latest_report)
    ]
    return older_reports[-1] if older_reports else None


def _migrate_analysis_number_entity(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Migrate the analysis-number entity away from the v0.2.2/v0.2.3 registry entry."""
    entity_registry = er.async_get(hass)
    old_unique_id = f"{entry.entry_id}{ANALYSIS_NUMBER_UNIQUE_ID_V1}"
    new_unique_id = f"{entry.entry_id}{ANALYSIS_NUMBER_UNIQUE_ID_V2}"

    if entity_registry.async_get_entity_id("sensor", DOMAIN, new_unique_id):
        return

    old_entity_id = entity_registry.async_get_entity_id(
        "sensor", DOMAIN, old_unique_id
    )
    if old_entity_id is None:
        return

    entity_registry.async_update_entity(
        old_entity_id,
        new_unique_id=new_unique_id,
    )
    hass.states.async_remove(old_entity_id)


def _stored_report_summary(entry: ConfigEntry) -> list[dict[str, Any]]:
    """Return compact metadata for all stored reports."""
    summaries: list[dict[str, Any]] = []
    for report in sorted(_reports(entry), key=_report_sort_key):
        metadata = report.get("metadata", {})
        summaries.append(
            {
                "analysis_number": metadata.get("analysis_number"),
                "analysis_date": metadata.get("analysis_date"),
                "sample_taken": metadata.get("sample_taken"),
                "tank_type": metadata.get("tank_type"),
                "provider": _report_provider(report),
                "provider_name": _report_provider_name(report),
                "report_type": _report_type(report),
            }
        )
    return summaries


def _laboratory_recommendations(
    report: dict[str, Any],
    measurements: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Build an explicit frontend payload for recommendations from the PDF.

    Keeping this separate from the generic ``measurements`` attribute gives the
    dashboard card a stable contract for laboratory-provided dosing advice.
    """
    items: list[dict[str, Any]] = []

    for measurement in measurements:
        recommendation = measurement.get("recommendation")
        if not isinstance(recommendation, dict):
            continue

        items.append(
            {
                "key": measurement.get("key"),
                "name": measurement.get("name"),
                "category": measurement.get("category"),
                "current": measurement.get("value"),
                "raw_value": measurement.get("raw_value"),
                "unit": measurement.get("unit"),
                "target": measurement.get("target"),
                "status": measurement.get("status"),
                "recommendation": dict(recommendation),
            }
        )

    report_text = report.get("product_recommendations")
    if not isinstance(report_text, str) or not report_text.strip():
        report_text = None

    if not items and report_text is None:
        return None

    return {
        "provider": _report_provider(report),
        "provider_name": _report_provider_name(report),
        "report_type": _report_type(report),
        "items": items,
        "report_text": report_text.strip() if report_text else None,
    }



_SEVERITY_RANK = {
    "ok": 0,
    "warning": 1,
    "critical": 2,
}


def _severity(measurement: dict[str, Any] | None) -> str:
    """Return one normalized severity label."""
    if measurement is None:
        return "unknown"
    value = measurement.get("status", {}).get("severity", "unknown")
    return str(value) if value else "unknown"


def _target_distance(value: Any, target: Any) -> float | None:
    """Return the distance of a numeric value from one target definition."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    if not isinstance(target, dict):
        return None

    target_type = target.get("type")
    numeric_value = float(value)

    if target_type == "exact":
        target_value = target.get("value")
        if not isinstance(target_value, (int, float)) or isinstance(
            target_value, bool
        ):
            return None
        return abs(numeric_value - float(target_value))

    if target_type == "range":
        minimum = target.get("min")
        maximum = target.get("max")
        if (
            not isinstance(minimum, (int, float))
            or isinstance(minimum, bool)
            or not isinstance(maximum, (int, float))
            or isinstance(maximum, bool)
        ):
            return None
        if numeric_value < float(minimum):
            return float(minimum) - numeric_value
        if numeric_value > float(maximum):
            return numeric_value - float(maximum)
        return 0.0

    if target_type == "upper_limit":
        maximum = target.get("max")
        if not isinstance(maximum, (int, float)) or isinstance(maximum, bool):
            return None
        return max(0.0, numeric_value - float(maximum))

    if target_type == "lower_limit":
        minimum = target.get("min")
        if not isinstance(minimum, (int, float)) or isinstance(minimum, bool):
            return None
        return max(0.0, float(minimum) - numeric_value)

    return None


def _analysis_change_items(
    current_report: dict[str, Any],
    previous_report: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Compare newest and previous values against one shared current target.

    Provider status labels are intentionally not compared here. Different
    laboratories can assign different severities or reference ranges to the
    same concentration. For a cross-provider comparison, both numeric values
    are therefore evaluated against the *current report's* normalized target.

    Non-numeric states such as ``n.n.``, ``n.g.`` or ``---`` are not treated as
    improvements or deteriorations because their distance from a numeric target
    cannot be established reliably.
    """
    if previous_report is None:
        return []

    current_measurements = _measurement_map(current_report)
    previous_measurements = _measurement_map(previous_report)
    items: list[dict[str, Any]] = []

    for key, current in current_measurements.items():
        previous = previous_measurements.get(key)
        if previous is None:
            continue

        current_value = current.get("value")
        previous_value = previous.get("value")
        target = current.get("target")

        current_distance = _target_distance(current_value, target)
        previous_distance = _target_distance(previous_value, target)

        # Without two numeric, target-comparable values there is no defensible
        # cross-provider improvement/worsening judgment.
        if current_distance is None or previous_distance is None:
            continue

        epsilon = max(
            abs(float(current_distance)),
            abs(float(previous_distance)),
            1.0,
        ) * 1e-9
        current_in_target = current_distance <= epsilon
        previous_in_target = previous_distance <= epsilon

        if previous_in_target and not current_in_target:
            kind = "new_issue"
        elif not previous_in_target and current_in_target:
            kind = "resolved"
        elif not previous_in_target and not current_in_target:
            if current_distance < previous_distance - epsilon:
                kind = "improved"
            elif current_distance > previous_distance + epsilon:
                kind = "worsened"
            else:
                continue
        else:
            # Both values are inside the current target range.
            continue

        current_severity = _severity(current)
        previous_severity = _severity(previous)

        items.append(
            {
                "kind": kind,
                "key": current.get("key"),
                "name": current.get("name"),
                "category": current.get("category"),
                "unit": current.get("unit"),
                "current": current_value,
                "current_raw_value": current.get("raw_value"),
                "previous": previous_value,
                "previous_raw_value": previous.get("raw_value"),
                "delta": _delta(current_value, previous_value),
                "current_severity": current_severity,
                "previous_severity": previous_severity,
                "status": current.get("status"),
                "previous_status": previous.get("status"),
                "target": target,
                "current_target_distance": current_distance,
                "previous_target_distance": previous_distance,
            }
        )

    priority = {
        "new_issue": 0,
        "worsened": 1,
        "resolved": 2,
        "improved": 3,
    }
    items.sort(
        key=lambda item: (
            priority.get(str(item.get("kind")), 9),
            -_SEVERITY_RANK.get(str(item.get("current_severity")), -1),
            str(item.get("name") or item.get("key") or ""),
        )
    )
    return items


def _numeric_direction(previous: float, current: float) -> str:
    """Return the numeric direction between two measured values."""
    delta = current - previous
    epsilon = max(abs(previous), abs(current), 1.0) * 1e-9
    if delta > epsilon:
        return "up"
    if delta < -epsilon:
        return "down"
    return "same"


def _analysis_trends(
    entry: ConfigEntry,
    current_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    """Return repeated same-direction measurement streaks across ICP reports.

    A trend is reported only after at least three numeric measurements of the
    same normalized analyte and unit move consecutively in one direction.
    This is a descriptive measurement trend, not a biological judgment.
    """
    reports = sorted(_reports(entry), key=_report_sort_key)
    if len(reports) < 3:
        return [], 0

    current_measurements = _measurement_map(current_report)
    trends: list[dict[str, Any]] = []

    for key, current in current_measurements.items():
        current_unit = current.get("unit")
        points: list[dict[str, Any]] = []

        for report in reports:
            measurement = _measurement_map(report).get(key)
            if measurement is None:
                continue
            if measurement.get("unit") != current_unit:
                continue

            value = measurement.get("value")
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
            ):
                continue

            metadata = report.get("metadata", {})
            points.append(
                {
                    "value": float(value),
                    "analysis_number": metadata.get("analysis_number"),
                    "analysis_date": metadata.get("analysis_date"),
                    "sample_taken": metadata.get("sample_taken"),
                    "provider": _report_provider(report),
                    "provider_name": _report_provider_name(report),
                    "report_type": _report_type(report),
                }
            )

        if len(points) < 3:
            continue

        latest_direction = _numeric_direction(
            points[-2]["value"],
            points[-1]["value"],
        )
        if latest_direction == "same":
            continue

        streak_count = 2
        index = len(points) - 2
        while index > 0:
            direction = _numeric_direction(
                points[index - 1]["value"],
                points[index]["value"],
            )
            if direction != latest_direction:
                break
            streak_count += 1
            index -= 1

        if streak_count < 3:
            continue

        first = points[-streak_count]
        latest = points[-1]
        delta = round(latest["value"] - first["value"], 6)

        trends.append(
            {
                "key": current.get("key"),
                "name": current.get("name"),
                "category": current.get("category"),
                "unit": current_unit,
                "direction": latest_direction,
                "measurement_count": streak_count,
                "first_value": first["value"],
                "current_value": latest["value"],
                "delta": 0.0 if delta == -0.0 else delta,
                "first_analysis_number": first.get("analysis_number"),
                "first_analysis_date": first.get("analysis_date"),
                "current_analysis_number": latest.get("analysis_number"),
                "current_analysis_date": latest.get("analysis_date"),
                "current_severity": _severity(current),
                "status": current.get("status"),
            }
        )

    trends.sort(
        key=lambda item: (
            -_SEVERITY_RANK.get(str(item.get("current_severity")), -1),
            -int(item.get("measurement_count") or 0),
            -abs(float(item.get("delta") or 0.0)),
            str(item.get("name") or item.get("key") or ""),
        )
    )

    total = len(trends)
    return trends[:8], total


def _analysis_insights(
    entry: ConfigEntry,
    current_report: dict[str, Any],
    previous_report: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Build a compact latest-change and multi-report trend payload."""
    if previous_report is None:
        return None

    previous_metadata = previous_report.get("metadata", {})
    changes = _analysis_change_items(current_report, previous_report)
    trends, trend_total = _analysis_trends(entry, current_report)

    counts = Counter(item["kind"] for item in changes)
    return {
        "compared_to": {
            "analysis_number": previous_metadata.get("analysis_number"),
            "analysis_date": previous_metadata.get("analysis_date"),
            "sample_taken": previous_metadata.get("sample_taken"),
            "provider": _report_provider(previous_report),
            "provider_name": _report_provider_name(previous_report),
            "report_type": _report_type(previous_report),
        },
        "status_change_counts": {
            "new_issue": counts.get("new_issue", 0),
            "worsened": counts.get("worsened", 0),
            "resolved": counts.get("resolved", 0),
            "improved": counts.get("improved", 0),
        },
        "changes": changes,
        "trends": trends,
        "trend_count": trend_total,
        "trend_items_limited": trend_total > len(trends),
    }



_PROFILE_CONTEXT_CARBONATE = "carbonate"
_PROFILE_CONTEXT_NUTRIENTS = "nutrients"
_PROFILE_CONTEXT_SALINITY = "salinity"

_PROFILE_CONTEXT_KEYS: dict[str, str] = {
    "alkalinitaet": _PROFILE_CONTEXT_CARBONATE,
    "calcium": _PROFILE_CONTEXT_CARBONATE,
    "salinitaet": _PROFILE_CONTEXT_SALINITY,
    "nitrat": _PROFILE_CONTEXT_NUTRIENTS,
    "phosphat": _PROFILE_CONTEXT_NUTRIENTS,
    "phosphat_photometrisch": _PROFILE_CONTEXT_NUTRIENTS,
    "gesamtphosphor_icp": _PROFILE_CONTEXT_NUTRIENTS,
    "gesamtphosphat_errechnet": _PROFILE_CONTEXT_NUTRIENTS,
}

_PROFILE_ATTENTION_HIGH = "high"
_PROFILE_ATTENTION_MEDIUM = "medium"

# This is intentionally a relevance map, not a target-range table. SPS/LPS are
# practical aquarium husbandry profiles rather than strict scientific taxa.
# The profile changes only which already-measured parameters Reef ICP brings
# to the user's attention. Laboratory status, targets and dosing remain intact.
_PROFILE_RELEVANCE: dict[str, dict[str, str]] = {
    STOCKING_PROFILE_MIXED_REEF: {
        _PROFILE_CONTEXT_CARBONATE: _PROFILE_ATTENTION_HIGH,
        _PROFILE_CONTEXT_NUTRIENTS: _PROFILE_ATTENTION_MEDIUM,
        _PROFILE_CONTEXT_SALINITY: _PROFILE_ATTENTION_HIGH,
    },
    STOCKING_PROFILE_SPS_DOMINANT: {
        _PROFILE_CONTEXT_CARBONATE: _PROFILE_ATTENTION_HIGH,
        _PROFILE_CONTEXT_NUTRIENTS: _PROFILE_ATTENTION_HIGH,
        _PROFILE_CONTEXT_SALINITY: _PROFILE_ATTENTION_HIGH,
    },
    STOCKING_PROFILE_LPS_DOMINANT: {
        _PROFILE_CONTEXT_CARBONATE: _PROFILE_ATTENTION_HIGH,
        _PROFILE_CONTEXT_NUTRIENTS: _PROFILE_ATTENTION_MEDIUM,
        _PROFILE_CONTEXT_SALINITY: _PROFILE_ATTENTION_HIGH,
    },
    STOCKING_PROFILE_SOFT_CORAL_DOMINANT: {
        _PROFILE_CONTEXT_NUTRIENTS: _PROFILE_ATTENTION_MEDIUM,
        _PROFILE_CONTEXT_SALINITY: _PROFILE_ATTENTION_HIGH,
    },
    STOCKING_PROFILE_FISH_ONLY: {
        _PROFILE_CONTEXT_NUTRIENTS: _PROFILE_ATTENTION_MEDIUM,
        _PROFILE_CONTEXT_SALINITY: _PROFILE_ATTENTION_HIGH,
    },
}


def _stocking_profile_context(
    measurement: dict[str, Any],
) -> str | None:
    """Return the conservative profile-context bucket for one measurement."""
    return _PROFILE_CONTEXT_KEYS.get(str(measurement.get("key") or ""))


def _stocking_profile_insights(
    stocking_profile: str | None,
    measurements: list[dict[str, Any]],
    analysis_insights: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Build contextual attention hints for the selected stocking profile.

    These hints never replace laboratory status, targets or dosing. They only
    highlight a deliberately small set of chemistry areas whose relevance can
    be defended without inventing SPS/LPS-specific target ranges.
    """
    if not stocking_profile or stocking_profile == STOCKING_PROFILE_OTHER:
        return None

    relevance = _PROFILE_RELEVANCE.get(stocking_profile)
    if not relevance:
        return None

    trend_map: dict[tuple[str, str], dict[str, Any]] = {}
    if isinstance(analysis_insights, dict):
        for trend in analysis_insights.get("trends", []):
            if not isinstance(trend, dict):
                continue
            trend_key = (
                str(trend.get("category") or "unknown"),
                str(trend.get("key") or "unknown"),
            )
            trend_map[trend_key] = trend

    items_by_key: dict[tuple[str, str], dict[str, Any]] = {}

    for measurement in measurements:
        context = _stocking_profile_context(measurement)
        attention = relevance.get(context) if context else None
        if attention is None:
            continue

        severity = _severity(measurement)
        current_issue = severity in {"warning", "critical"}
        trend = trend_map.get(_measurement_key(measurement))

        # Medium-relevance areas are surfaced only when the current report is
        # already abnormal. High-relevance areas may also surface a repeated
        # numeric trend while the current value is still in range.
        include_trend = (
            trend is not None
            and (
                attention == _PROFILE_ATTENTION_HIGH
                or current_issue
            )
        )
        if not current_issue and not include_trend:
            continue

        current_target_distance = _target_distance(
            measurement.get("value"),
            measurement.get("target"),
        )

        item = {
            "key": measurement.get("key"),
            "name": measurement.get("name"),
            "category": measurement.get("category"),
            "unit": measurement.get("unit"),
            "context": context,
            "attention": attention,
            "current": measurement.get("value"),
            "current_raw_value": measurement.get("raw_value"),
            "severity": severity,
            "status": measurement.get("status"),
            "target": measurement.get("target"),
            "current_issue": current_issue,
            "target_comparable": current_target_distance is not None,
            "current_target_distance": current_target_distance,
        }

        if include_trend and trend is not None:
            item.update(
                {
                    "trend_direction": trend.get("direction"),
                    "trend_measurement_count": trend.get("measurement_count"),
                    "trend_first_value": trend.get("first_value"),
                    "trend_current_value": trend.get("current_value"),
                }
            )

        items_by_key[_measurement_key(measurement)] = item

    items = list(items_by_key.values())
    attention_rank = {
        _PROFILE_ATTENTION_HIGH: 0,
        _PROFILE_ATTENTION_MEDIUM: 1,
    }
    severity_rank = {
        "critical": 0,
        "warning": 1,
        "ok": 2,
        "unknown": 3,
    }
    items.sort(
        key=lambda item: (
            attention_rank.get(str(item.get("attention")), 9),
            severity_rank.get(str(item.get("severity")), 9),
            0 if item.get("trend_direction") else 1,
            str(item.get("name") or item.get("key") or ""),
        )
    )

    if not items:
        return None

    total = len(items)
    visible_items = items[:6]
    context_counts = Counter(str(item.get("context")) for item in items)

    return {
        "profile": stocking_profile,
        "profile_name": STOCKING_PROFILE_NAMES.get(
            stocking_profile,
            stocking_profile,
        ),
        "mode": "context_only",
        "items": visible_items,
        "item_count": total,
        "items_limited": total > len(visible_items),
        "context_counts": {
            "carbonate": context_counts.get(_PROFILE_CONTEXT_CARBONATE, 0),
            "nutrients": context_counts.get(_PROFILE_CONTEXT_NUTRIENTS, 0),
            "salinity": context_counts.get(_PROFILE_CONTEXT_SALINITY, 0),
        },
    }



def _action_plan(
    report: dict[str, Any],
    measurements: list[dict[str, Any]],
    laboratory_recommendations: dict[str, Any] | None,
    supply_recommendations: dict[str, Any] | None,
    stocking_profile_insights: dict[str, Any] | None,
    analysis_insights: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Build a compact plan from already existing recommendation sources.

    The plan never invents a new dose. Laboratory instructions and Reef ICP
    supply-system calculations remain separate source actions. If both sources
    provide an action for the same analyte, the frontend can warn the user not
    to add the doses together.
    """
    measurement_by_key = {
        str(measurement.get("key") or ""): measurement
        for measurement in measurements
        if measurement.get("key")
    }
    items_by_key: dict[str, dict[str, Any]] = {}

    def ensure_item(key: str, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
        measurement = measurement_by_key.get(key, fallback or {})
        item = items_by_key.get(key)
        if item is None:
            item = {
                "key": key,
                "name": measurement.get("name") or key,
                "category": measurement.get("category"),
                "unit": measurement.get("unit"),
                "current": measurement.get("value"),
                "current_raw_value": measurement.get("raw_value"),
                "severity": _severity(measurement),
                "status": measurement.get("status"),
                "target": measurement.get("target"),
                "actions": [],
                "signals": [],
            }
            items_by_key[key] = item
        return item

    # 1) Laboratory-provided instructions, preserved as their own source.
    if isinstance(laboratory_recommendations, dict):
        laboratory_source_name = (
            laboratory_recommendations.get("provider_name")
            or laboratory_recommendations.get("provider")
            or "Laboratory"
        )
        for lab_item in laboratory_recommendations.get("items", []):
            if not isinstance(lab_item, dict):
                continue
            key = str(lab_item.get("key") or "")
            recommendation = lab_item.get("recommendation")
            if not key or not isinstance(recommendation, dict):
                continue

            action_type = str(recommendation.get("type") or "")
            if action_type not in {"dose", "water_change"}:
                continue

            item = ensure_item(key, lab_item)
            item["actions"].append(
                {
                    "source": "laboratory",
                    "source_name": laboratory_source_name,
                    "action": action_type,
                    "product": recommendation.get("product"),
                    "amount_ml": recommendation.get("amount_ml"),
                    "days": recommendation.get("days"),
                    "one_time_ml": recommendation.get("one_time_ml"),
                    "daily_ml": recommendation.get("daily_ml"),
                    "aquarium_volume_l": recommendation.get("aquarium_volume_l"),
                }
            )

    # 2) Reef ICP calculations for the selected supply system.
    if isinstance(supply_recommendations, dict):
        supply_source_name = (
            supply_recommendations.get("system_name")
            or supply_recommendations.get("system")
            or "Supply system"
        )
        for supply_item in supply_recommendations.get("items", []):
            if not isinstance(supply_item, dict):
                continue

            key = str(supply_item.get("key") or "")
            action_type = str(supply_item.get("action") or "")
            if not key or action_type not in {
                "correction_dose",
                "reduce_or_pause",
                "official_calculator",
                "requires_icp_ms",
            }:
                continue

            item = ensure_item(key, supply_item)
            item["actions"].append(
                {
                    "source": "supply_system",
                    "source_name": supply_source_name,
                    "action": action_type,
                    "product": supply_item.get("product"),
                    "solution": supply_item.get("solution"),
                    "dose_amount": supply_item.get("dose_amount"),
                    "dose_unit": supply_item.get("dose_unit"),
                    "split_days": supply_item.get("split_days"),
                    "daily_dose_amount": supply_item.get("daily_dose_amount"),
                    "daily_limit_known": supply_item.get("daily_limit_known"),
                    "source_url": supply_item.get("source_url"),
                }
            )

    # 3) Stocking-profile context. Inside the action plan, profile context is
    # only added when it contributes a repeated numeric trend. A plain
    # "relevant / observe" signal already exists in the dedicated profile panel
    # and would add noise here without changing the next action.
    if isinstance(stocking_profile_insights, dict):
        for profile_item in stocking_profile_insights.get("items", []):
            if not isinstance(profile_item, dict):
                continue

            trend_direction = profile_item.get("trend_direction")
            if trend_direction not in {"up", "down"}:
                continue

            key = str(profile_item.get("key") or "")
            if not key:
                continue

            item = ensure_item(key, profile_item)
            item["signals"].append(
                {
                    "source": "stocking_profile",
                    "attention": profile_item.get("attention"),
                    "context": profile_item.get("context"),
                    "trend_direction": trend_direction,
                    "trend_measurement_count": profile_item.get(
                        "trend_measurement_count"
                    ),
                }
            )

    # 4) Latest-vs-previous comparison. Only changes needing attention are
    # promoted into the action plan. Improvements stay in the comparison panel.
    if isinstance(analysis_insights, dict):
        for change in analysis_insights.get("changes", []):
            if not isinstance(change, dict):
                continue
            if change.get("kind") not in {"new_issue", "worsened"}:
                continue
            key = str(change.get("key") or "")
            if not key:
                continue

            item = ensure_item(key, change)
            item["signals"].append(
                {
                    "source": "comparison",
                    "kind": change.get("kind"),
                    "previous": change.get("previous"),
                    "previous_raw_value": change.get("previous_raw_value"),
                }
            )

    if not items_by_key:
        return None

    actionable_sources = {"laboratory", "supply_system"}

    for item in items_by_key.values():
        source_types = {
            str(action.get("source"))
            for action in item["actions"]
            if action.get("source") in actionable_sources
        }
        item["multiple_action_sources"] = len(source_types) > 1
        item["has_action"] = bool(item["actions"])

    severity_rank = {
        "critical": 0,
        "warning": 1,
        "unknown": 2,
        "ok": 3,
    }
    items = sorted(
        items_by_key.values(),
        key=lambda item: (
            0 if item.get("has_action") else 1,
            severity_rank.get(str(item.get("severity")), 9),
            0 if item.get("multiple_action_sources") else 1,
            str(item.get("name") or item.get("key") or ""),
        ),
    )

    metadata = report.get("metadata", {})
    total = len(items)
    visible_items = items[:8]
    visible_action_items = [
        item for item in visible_items if item.get("has_action")
    ]
    visible_review_items = [
        item for item in visible_items if not item.get("has_action")
    ]
    action_item_count = sum(1 for item in items if item.get("has_action"))
    review_item_count = sum(1 for item in items if not item.get("has_action"))

    return {
        "analysis_number": metadata.get("analysis_number"),
        "analysis_date": metadata.get("analysis_date"),
        "provider": _report_provider(report),
        "provider_name": _report_provider_name(report),
        "report_type": _report_type(report),
        # `items` remains for backwards compatibility. The explicit groups make
        # the intended UI hierarchy available to other consumers as well.
        "items": visible_items,
        "action_items": visible_action_items,
        "review_items": visible_review_items,
        "item_count": total,
        "items_limited": total > len(visible_items),
        "action_item_count": action_item_count,
        "review_item_count": review_item_count,
        "visible_action_item_count": len(visible_action_items),
        "visible_review_item_count": len(visible_review_items),
    }


def _status_counts(report: dict[str, Any]) -> dict[str, int]:
    """Count provider-normalized status severities."""
    counts = Counter(
        measurement.get("status", {}).get("severity", "unknown")
        for measurement in report.get("measurements", [])
    )
    return {
        "ok": counts.get("ok", 0),
        "warning": counts.get("warning", 0),
        "critical": counts.get("critical", 0),
        "unknown": counts.get("unknown", 0),
    }


def _overall_status(report: dict[str, Any]) -> str:
    """Return the worst status from a report."""
    counts = _status_counts(report)
    if counts["critical"]:
        return "critical"
    if counts["warning"]:
        return "warning"
    if counts["unknown"]:
        return "unknown"
    return "ok"


def _display_value(measurement: dict[str, Any]) -> str:
    """Return a human-readable value including provider non-detect states."""
    raw_value = measurement.get("raw_value")
    if raw_value == "n.n.":
        return "Nicht nachweisbar"
    if raw_value in {"n.b.", "n.g."}:
        return "Nicht bestimmt"
    if raw_value is None:
        return "Unbekannt"

    unit = measurement.get("unit")
    return f"{raw_value} {unit}" if unit else str(raw_value)


def _measurement_key(measurement: dict[str, Any]) -> tuple[str, str]:
    """Return a stable identity for one measurement."""
    return (
        str(measurement.get("category", "unknown")),
        str(measurement.get("key", "unknown")),
    )


def _measurement_map(report: dict[str, Any] | None) -> dict[tuple[str, str], dict[str, Any]]:
    """Index report measurements by category and key."""
    if report is None:
        return {}

    return {
        _measurement_key(measurement): measurement
        for measurement in report.get("measurements", [])
    }


def _latest_measurement_sources(
    entry: ConfigEntry,
    latest_report: dict[str, Any],
) -> list[tuple[dict[str, Any], dict[str, Any], bool]]:
    """Return the newest available result for every analyte ever imported.

    A provider may omit parameters that another provider measured. Keeping the
    newest available result for each analyte prevents those stable Home
    Assistant entities from becoming unavailable after a cross-provider import.
    The boolean marks whether the analyte is actually present in the newest
    report, so carried-forward values can never be mistaken for fresh results.
    """
    current_keys = set(_measurement_map(latest_report))
    seen: set[tuple[str, str]] = set()
    sources: list[tuple[dict[str, Any], dict[str, Any], bool]] = []

    for report in sorted(_reports(entry), key=_report_sort_key, reverse=True):
        for measurement in report.get("measurements", []):
            key = _measurement_key(measurement)
            if key in seen:
                continue
            seen.add(key)
            sources.append((report, measurement, key in current_keys))

    return sources


def _delta(current_value: Any, previous_value: Any) -> float | None:
    """Return the numeric difference when both values are measurable."""
    if not isinstance(current_value, (int, float)):
        return None
    if not isinstance(previous_value, (int, float)):
        return None

    result = round(float(current_value) - float(previous_value), 6)
    return 0.0 if result == -0.0 else result


def _trend(delta: float | None) -> str | None:
    """Return a simple trend label for dashboard cards."""
    if delta is None:
        return None
    if delta > 0:
        return "up"
    if delta < 0:
        return "down"
    return "same"


def _measurement_with_history(
    measurement: dict[str, Any],
    previous_measurements: dict[tuple[str, str], dict[str, Any]],
    previous_report: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return a copy of a measurement enriched with previous-report data."""
    enriched = dict(measurement)
    previous = previous_measurements.get(_measurement_key(measurement))

    if previous is None or previous_report is None:
        enriched.update(
            {
                "has_previous": False,
                "previous_value": None,
                "previous_raw_value": None,
                "previous_display_value": None,
                "previous_analysis_number": None,
                "previous_analysis_date": None,
                "previous_sample_taken": None,
                "previous_provider": None,
                "previous_provider_name": None,
                "delta": None,
                "trend": None,
            }
        )
        return enriched

    previous_metadata = previous_report.get("metadata", {})
    delta = _delta(measurement.get("value"), previous.get("value"))

    enriched.update(
        {
            "has_previous": True,
            "previous_value": previous.get("value"),
            "previous_raw_value": previous.get("raw_value"),
            "previous_display_value": _display_value(previous),
            "previous_analysis_number": previous_metadata.get("analysis_number"),
            "previous_analysis_date": previous_metadata.get("analysis_date"),
            "previous_sample_taken": previous_metadata.get("sample_taken"),
            "previous_provider": _report_provider(previous_report),
            "previous_provider_name": _report_provider_name(previous_report),
            "delta": delta,
            "trend": _trend(delta),
        }
    )
    return enriched


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Reef ICP sensors."""
    _migrate_analysis_number_entity(hass, entry)

    report = _latest_report(entry)
    previous_report = _previous_report(entry, report)
    previous_measurements = _measurement_map(previous_report)

    # The dashboard remains a strict view of the newest report. This prevents
    # carried-forward values from looking as though the current laboratory
    # measured them.
    enriched_measurements = [
        _measurement_with_history(
            measurement,
            previous_measurements,
            previous_report,
        )
        for measurement in report.get("measurements", [])
    ]
    for measurement in enriched_measurements:
        measurement["historical_statistic_id"] = statistic_id_for(
            entry, measurement
        )

    enriched_current = {
        _measurement_key(measurement): measurement
        for measurement in enriched_measurements
    }

    entities: list[SensorEntity] = [
        ReefReportSensor(entry, report, previous_report, enriched_measurements),
        ReefAnalysisDateSensor(entry, report),
        ReefAnalysisNumberSensor(entry, report),
    ]

    # Individual Home Assistant entities are stable across providers. If the
    # newest report omits an analyte, expose its newest available result from
    # an older report and mark it explicitly as not included in the current
    # report. A current n.n./n.b./n.g./--- result still wins because the
    # analyte is present in the newest report.
    for source_report, source_measurement, included_in_current in (
        _latest_measurement_sources(entry, report)
    ):
        key = _measurement_key(source_measurement)
        measurement = enriched_current.get(key, source_measurement)
        entities.append(
            ReefMeasurementSensor(
                entry,
                source_report,
                measurement,
                current_report=report,
                included_in_current_report=included_in_current,
            )
        )

    async_add_entities(entities)


class ReefBaseSensor(SensorEntity):
    """Base sensor for imported ICP report data."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, report: dict[str, Any]) -> None:
        self._entry = entry
        self._report = report
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Reef ICP",
            model="Multi-provider ICP Analysis",
        )


class ReefReportSensor(ReefBaseSensor):
    """Summary sensor and data source for the custom dashboard card."""

    _attr_name = "ICP Status"
    _attr_icon = "mdi:test-tube"

    def __init__(
        self,
        entry: ConfigEntry,
        report: dict[str, Any],
        previous_report: dict[str, Any] | None,
        measurements: list[dict[str, Any]],
    ) -> None:
        super().__init__(entry, report)
        self._previous_report = previous_report
        self._measurements = measurements
        self._attr_unique_id = f"{entry.entry_id}_report"

    @property
    @override
    def native_value(self) -> StateType:
        return _overall_status(self._report)

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        metadata = self._report.get("metadata", {})
        previous_metadata = (
            self._previous_report.get("metadata", {})
            if self._previous_report is not None
            else {}
        )

        profile = _aquarium_profile(self._entry)
        analysis_insights = _analysis_insights(
            self._entry,
            self._report,
            self._previous_report,
        )
        stocking_profile_insights = _stocking_profile_insights(
            profile.get("stocking_profile"),
            self._measurements,
            analysis_insights,
        )
        laboratory_recommendations = _laboratory_recommendations(
            self._report,
            self._measurements,
        )
        supply_recommendations = build_supply_recommendations(
            profile.get("supply_system"),
            profile.get("aquarium_volume_l"),
            self._measurements,
            _report_type(self._report),
        )
        action_plan = _action_plan(
            self._report,
            self._measurements,
            laboratory_recommendations,
            supply_recommendations,
            stocking_profile_insights,
            analysis_insights,
        )

        return {
            **profile,
            "analysis_number": metadata.get("analysis_number"),
            "analysis_date": metadata.get("analysis_date"),
            "sample_taken": metadata.get("sample_taken"),
            "tank_type": metadata.get("tank_type"),
            "provider": _report_provider(self._report),
            "provider_name": _report_provider_name(self._report),
            "report_type": _report_type(self._report),
            "previous_analysis_number": previous_metadata.get("analysis_number"),
            "previous_analysis_date": previous_metadata.get("analysis_date"),
            "previous_sample_taken": previous_metadata.get("sample_taken"),
            "previous_provider": _report_provider(self._previous_report)
            if self._previous_report is not None
            else None,
            "previous_provider_name": _report_provider_name(self._previous_report)
            if self._previous_report is not None
            else None,
            "previous_report_type": _report_type(self._previous_report),
            "status_counts": _status_counts(self._report),
            "analysis_insights": analysis_insights,
            "stocking_profile_insights": stocking_profile_insights,
            "measurements": self._measurements,
            "interpretation": self._report.get("interpretation"),
            "product_recommendations": self._report.get("product_recommendations"),
            "laboratory_recommendations": laboratory_recommendations,
            "supply_recommendations": supply_recommendations,
            "action_plan": action_plan,
            "stored_report_count": len(_reports(self._entry)),
            "stored_reports": _stored_report_summary(self._entry),
        }


class ReefAnalysisDateSensor(ReefBaseSensor):
    """Date of the latest imported ICP analysis."""

    _attr_name = "Analysis date"
    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:calendar"

    def __init__(self, entry: ConfigEntry, report: dict[str, Any]) -> None:
        super().__init__(entry, report)
        self._attr_unique_id = f"{entry.entry_id}_analysis_date"

    @property
    @override
    def native_value(self) -> date | None:
        value = self._report.get("metadata", {}).get("analysis_date")
        return date.fromisoformat(value) if value else None

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "analysis_number": self._report.get("metadata", {}).get("analysis_number"),
            "sample_taken": self._report.get("metadata", {}).get("sample_taken"),
            "tank_type": self._report.get("metadata", {}).get("tank_type"),
            "provider": _report_provider(self._report),
            "provider_name": _report_provider_name(self._report),
        }


class ReefAnalysisNumberSensor(ReefBaseSensor):
    """Analysis number of the latest imported report."""

    _attr_name = "Analysis number"
    _attr_icon = "mdi:identifier"

    def __init__(self, entry: ConfigEntry, report: dict[str, Any]) -> None:
        super().__init__(entry, report)
        self._attr_unique_id = f"{entry.entry_id}{ANALYSIS_NUMBER_UNIQUE_ID_V2}"

        metadata = report.get("metadata", {})
        self._attr_native_value = metadata.get("analysis_number")
        self._attr_extra_state_attributes = {
            "analysis_date": metadata.get("analysis_date"),
            "sample_taken": metadata.get("sample_taken"),
            "tank_type": metadata.get("tank_type"),
            "provider": _report_provider(report),
            "provider_name": _report_provider_name(report),
            "report_type": _report_type(report),
        }


class ReefMeasurementSensor(ReefBaseSensor):
    """Newest available result for one analyte across all stored reports."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        entry: ConfigEntry,
        report: dict[str, Any],
        measurement: dict[str, Any],
        *,
        current_report: dict[str, Any],
        included_in_current_report: bool,
    ) -> None:
        super().__init__(entry, report)
        self._measurement = measurement
        self._current_report = current_report
        self._included_in_current_report = included_in_current_report

        category = measurement.get("category", "unknown")
        key = measurement.get("key", "unknown")
        self._attr_unique_id = f"{entry.entry_id}_{category}_{key}"
        self._attr_name = measurement.get("name", key)
        self._attr_native_unit_of_measurement = measurement.get("unit")
        self._attr_icon = "mdi:flask"

    @property
    @override
    def native_value(self) -> StateType:
        return self._measurement.get("value")

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        source_metadata = self._report.get("metadata", {})
        current_metadata = self._current_report.get("metadata", {})

        return {
            "category": self._measurement.get("category"),
            "provider": _report_provider(self._report),
            "provider_name": _report_provider_name(self._report),
            "report_type": _report_type(self._report),
            "raw_value": self._measurement.get("raw_value"),
            "source_raw_value": self._measurement.get("source_raw_value"),
            "source_unit": self._measurement.get("source_unit"),
            "value_qualifier": self._measurement.get("value_qualifier"),
            "value_bound": self._measurement.get("value_bound"),
            "display_value": _display_value(self._measurement),
            "detected": self._measurement.get("detected"),
            "determined": self._measurement.get("determined"),
            "target": self._measurement.get("target"),
            "status": self._measurement.get("status"),
            "recommendation": self._measurement.get("recommendation"),
            # These existing attributes describe the report that actually
            # supplied the sensor state.
            "analysis_number": source_metadata.get("analysis_number"),
            "analysis_date": source_metadata.get("analysis_date"),
            "sample_taken": source_metadata.get("sample_taken"),
            # v0.6.1: explicitly distinguish a carried-forward result from a
            # value that was really included in the newest ICP.
            "included_in_current_report": self._included_in_current_report,
            "last_measured_analysis_number": source_metadata.get("analysis_number"),
            "last_measured_analysis_date": source_metadata.get("analysis_date"),
            "last_measured_sample_taken": source_metadata.get("sample_taken"),
            "last_measured_provider": _report_provider(self._report),
            "last_measured_provider_name": _report_provider_name(self._report),
            "last_measured_report_type": _report_type(self._report),
            "current_analysis_number": current_metadata.get("analysis_number"),
            "current_analysis_date": current_metadata.get("analysis_date"),
            "current_sample_taken": current_metadata.get("sample_taken"),
            "current_provider": _report_provider(self._current_report),
            "current_provider_name": _report_provider_name(self._current_report),
            "current_report_type": _report_type(self._current_report),
            "has_previous": self._measurement.get("has_previous"),
            "previous_value": self._measurement.get("previous_value"),
            "previous_raw_value": self._measurement.get("previous_raw_value"),
            "previous_display_value": self._measurement.get(
                "previous_display_value"
            ),
            "previous_analysis_number": self._measurement.get(
                "previous_analysis_number"
            ),
            "previous_analysis_date": self._measurement.get(
                "previous_analysis_date"
            ),
            "previous_sample_taken": self._measurement.get(
                "previous_sample_taken"
            ),
            "previous_provider": self._measurement.get("previous_provider"),
            "previous_provider_name": self._measurement.get(
                "previous_provider_name"
            ),
            "delta": self._measurement.get("delta"),
            "trend": self._measurement.get("trend"),
            "historical_statistic_id": statistic_id_for(
                self._entry, self._measurement
            ),
        }

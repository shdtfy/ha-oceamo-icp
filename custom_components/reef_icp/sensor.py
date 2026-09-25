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
    STOCKING_PROFILE_NAMES,
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
        supply_recommendations = build_supply_recommendations(
            profile.get("supply_system"),
            profile.get("aquarium_volume_l"),
            self._measurements,
            _report_type(self._report),
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
            "measurements": self._measurements,
            "interpretation": self._report.get("interpretation"),
            "product_recommendations": self._report.get("product_recommendations"),
            "laboratory_recommendations": _laboratory_recommendations(
                self._report,
                self._measurements,
            ),
            "supply_recommendations": supply_recommendations,
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

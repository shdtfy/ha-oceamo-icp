"""Sensor platform for Oceamo ICP."""

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

from .const import CONF_REPORTS, DOMAIN
from .statistics import statistic_id_for

ANALYSIS_NUMBER_UNIQUE_ID_V1 = "_analysis_number"
ANALYSIS_NUMBER_UNIQUE_ID_V2 = "_analysis_number_v2"


def _reports(entry: ConfigEntry) -> list[dict[str, Any]]:
    """Return all stored reports."""
    return list(entry.options.get(CONF_REPORTS, []))


def _report_sort_key(report: dict[str, Any]) -> str:
    """Return the chronological sort key used by the integration."""
    metadata = report.get("metadata", {})
    return metadata.get("analysis_date", "")


def _latest_report(entry: ConfigEntry) -> dict[str, Any]:
    """Return the newest stored report."""
    reports = _reports(entry)
    return max(reports, key=_report_sort_key)


def _previous_report(
    entry: ConfigEntry, latest_report: dict[str, Any]
) -> dict[str, Any] | None:
    """Return the report immediately before the latest one."""
    latest_number = latest_report.get("metadata", {}).get("analysis_number")
    reports = sorted(_reports(entry), key=_report_sort_key)

    older_reports = [
        report
        for report in reports
        if report.get("metadata", {}).get("analysis_number") != latest_number
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
            }
        )
    return summaries


def _status_counts(report: dict[str, Any]) -> dict[str, int]:
    """Count Oceamo status severities."""
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
    """Return a human-readable value including Oceamo non-detect states."""
    raw_value = measurement.get("raw_value")
    if raw_value == "n.n.":
        return "Nicht nachweisbar"
    if raw_value == "n.b.":
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
    """Set up Oceamo ICP sensors."""
    _migrate_analysis_number_entity(hass, entry)

    report = _latest_report(entry)
    previous_report = _previous_report(entry, report)
    previous_measurements = _measurement_map(previous_report)

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

    entities: list[SensorEntity] = [
        OceamoReportSensor(entry, report, previous_report, enriched_measurements),
        OceamoAnalysisDateSensor(entry, report),
        OceamoAnalysisNumberSensor(entry, report),
    ]
    entities.extend(
        OceamoMeasurementSensor(entry, report, measurement)
        for measurement in enriched_measurements
    )
    async_add_entities(entities)


class OceamoBaseSensor(SensorEntity):
    """Base sensor for imported Oceamo report data."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, report: dict[str, Any]) -> None:
        self._entry = entry
        self._report = report
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Oceamo",
            model="ICP Analysis",
        )


class OceamoReportSensor(OceamoBaseSensor):
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

        return {
            "analysis_number": metadata.get("analysis_number"),
            "analysis_date": metadata.get("analysis_date"),
            "sample_taken": metadata.get("sample_taken"),
            "tank_type": metadata.get("tank_type"),
            "previous_analysis_number": previous_metadata.get("analysis_number"),
            "previous_analysis_date": previous_metadata.get("analysis_date"),
            "previous_sample_taken": previous_metadata.get("sample_taken"),
            "status_counts": _status_counts(self._report),
            "measurements": self._measurements,
            "interpretation": self._report.get("interpretation"),
            "product_recommendations": self._report.get("product_recommendations"),
            "stored_report_count": len(_reports(self._entry)),
            "stored_reports": _stored_report_summary(self._entry),
        }


class OceamoAnalysisDateSensor(OceamoBaseSensor):
    """Date of the latest Oceamo analysis."""

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
        }


class OceamoAnalysisNumberSensor(OceamoBaseSensor):
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
        }


class OceamoMeasurementSensor(OceamoBaseSensor):
    """One measurement from the latest report."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        entry: ConfigEntry,
        report: dict[str, Any],
        measurement: dict[str, Any],
    ) -> None:
        super().__init__(entry, report)
        self._measurement = measurement

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
        return {
            "category": self._measurement.get("category"),
            "raw_value": self._measurement.get("raw_value"),
            "display_value": _display_value(self._measurement),
            "detected": self._measurement.get("detected"),
            "determined": self._measurement.get("determined"),
            "target": self._measurement.get("target"),
            "status": self._measurement.get("status"),
            "analysis_number": self._report.get("metadata", {}).get("analysis_number"),
            "analysis_date": self._report.get("metadata", {}).get("analysis_date"),
            "sample_taken": self._report.get("metadata", {}).get("sample_taken"),
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
            "delta": self._measurement.get("delta"),
            "trend": self._measurement.get("trend"),
            "historical_statistic_id": statistic_id_for(
                self._entry, self._measurement
            ),
        }

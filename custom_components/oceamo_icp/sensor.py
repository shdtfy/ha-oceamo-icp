"""Sensor platform for Oceamo ICP."""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any, override

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import CONF_REPORTS, DOMAIN
from .statistics import statistic_id_for


def _reports(entry: ConfigEntry) -> list[dict[str, Any]]:
    return list(entry.options.get(CONF_REPORTS, []))


def _latest_report(entry: ConfigEntry) -> dict[str, Any]:
    reports = _reports(entry)
    return max(
        reports,
        key=lambda item: item.get("metadata", {}).get("analysis_date", ""),
    )


def _stored_report_summary(entry: ConfigEntry) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for report in sorted(
        _reports(entry),
        key=lambda item: item.get("metadata", {}).get("analysis_date", ""),
    ):
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
    counts = _status_counts(report)
    if counts["critical"]:
        return "critical"
    if counts["warning"]:
        return "warning"
    if counts["unknown"]:
        return "unknown"
    return "ok"


def _display_value(measurement: dict[str, Any]) -> str:
    raw_value = measurement.get("raw_value")
    if raw_value == "n.n.":
        return "Nicht nachweisbar"
    if raw_value == "n.b.":
        return "Nicht bestimmt"
    if raw_value is None:
        return "Unbekannt"
    unit = measurement.get("unit")
    return f"{raw_value} {unit}" if unit else str(raw_value)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    report = _latest_report(entry)
    entities: list[SensorEntity] = [
        OceamoReportSensor(entry, report),
        OceamoAnalysisDateSensor(entry, report),
        OceamoAnalysisNumberSensor(entry, report),
    ]
    entities.extend(
        OceamoMeasurementSensor(entry, report, measurement)
        for measurement in report.get("measurements", [])
    )
    async_add_entities(entities)


class OceamoBaseSensor(SensorEntity):
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
    _attr_name = "ICP Status"
    _attr_icon = "mdi:test-tube"

    def __init__(self, entry: ConfigEntry, report: dict[str, Any]) -> None:
        super().__init__(entry, report)
        self._attr_unique_id = f"{entry.entry_id}_report"

    @property
    @override
    def native_value(self) -> StateType:
        return _overall_status(self._report)

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        metadata = self._report.get("metadata", {})
        return {
            "analysis_number": metadata.get("analysis_number"),
            "analysis_date": metadata.get("analysis_date"),
            "sample_taken": metadata.get("sample_taken"),
            "tank_type": metadata.get("tank_type"),
            "status_counts": _status_counts(self._report),
            "measurements": self._report.get("measurements", []),
            "interpretation": self._report.get("interpretation"),
            "product_recommendations": self._report.get("product_recommendations"),
            "stored_report_count": len(_reports(self._entry)),
            "stored_reports": _stored_report_summary(self._entry),
        }


class OceamoAnalysisDateSensor(OceamoBaseSensor):
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
        self._attr_unique_id = f"{entry.entry_id}_analysis_number"
        metadata = report.get("metadata", {})
        self._attr_native_value = metadata.get("analysis_number")
        self._attr_extra_state_attributes = {
            "analysis_date": metadata.get("analysis_date"),
            "sample_taken": metadata.get("sample_taken"),
            "tank_type": metadata.get("tank_type"),
        }


class OceamoMeasurementSensor(OceamoBaseSensor):
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
            "historical_statistic_id": statistic_id_for(
                self._entry, self._measurement
            ),
        }

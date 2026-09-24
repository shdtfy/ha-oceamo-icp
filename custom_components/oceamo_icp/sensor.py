"""Sensor platform for Oceamo ICP."""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any, override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import CONF_REPORTS, DOMAIN


def _reports(entry: ConfigEntry) -> list[dict[str, Any]]:
    """Return stored reports."""
    return list(entry.options.get(CONF_REPORTS, []))


def _latest_report(entry: ConfigEntry) -> dict[str, Any]:
    """Return the newest stored report by analysis date."""
    reports = _reports(entry)
    return max(
        reports,
        key=lambda item: item.get("metadata", {}).get("analysis_date", ""),
    )


def _status_counts(report: dict[str, Any]) -> dict[str, int]:
    """Count status severities in a report."""
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
    """Return the worst status in the latest report."""
    counts = _status_counts(report)
    if counts["critical"]:
        return "critical"
    if counts["warning"]:
        return "warning"
    if counts["unknown"]:
        return "unknown"
    return "ok"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Oceamo ICP sensors."""
    report = _latest_report(entry)

    entities: list[SensorEntity] = [
        OceamoReportSensor(entry, report),
        OceamoAnalysisDateSensor(entry, report),
    ]
    entities.extend(
        OceamoMeasurementSensor(entry, report, measurement)
        for measurement in report.get("measurements", [])
    )
    async_add_entities(entities)


class OceamoBaseSensor(SensorEntity):
    """Base Oceamo sensor."""

    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, report: dict[str, Any]) -> None:
        """Initialize base sensor."""
        self._entry = entry
        self._report = report
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Oceamo",
            model="ICP Analysis",
        )


class OceamoReportSensor(OceamoBaseSensor):
    """Summary/report sensor used by the future dashboard card."""

    _attr_name = "ICP Status"
    _attr_icon = "mdi:test-tube"

    def __init__(self, entry: ConfigEntry, report: dict[str, Any]) -> None:
        """Initialize report sensor."""
        super().__init__(entry, report)
        self._attr_unique_id = f"{entry.entry_id}_report"

    @property
    @override
    def native_value(self) -> StateType:
        """Return overall report status."""
        return _overall_status(self._report)

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return full report data for dashboards and automations."""
        metadata = self._report.get("metadata", {})
        return {
            "analysis_number": metadata.get("analysis_number"),
            "analysis_date": metadata.get("analysis_date"),
            "sample_taken": metadata.get("sample_taken"),
            "tank_type": metadata.get("tank_type"),
            "status_counts": _status_counts(self._report),
            "measurements": self._report.get("measurements", []),
            "interpretation": self._report.get("interpretation"),
            "product_recommendations": self._report.get(
                "product_recommendations"
            ),
            "stored_report_count": len(_reports(self._entry)),
        }


class OceamoAnalysisDateSensor(OceamoBaseSensor):
    """Date of the latest imported analysis."""

    _attr_name = "Analysis date"
    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:calendar"

    def __init__(self, entry: ConfigEntry, report: dict[str, Any]) -> None:
        """Initialize date sensor."""
        super().__init__(entry, report)
        self._attr_unique_id = f"{entry.entry_id}_analysis_date"

    @property
    @override
    def native_value(self) -> date | None:
        """Return analysis date."""
        value = self._report.get("metadata", {}).get("analysis_date")
        return date.fromisoformat(value) if value else None

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return report metadata."""
        return {
            "analysis_number": self._report.get("metadata", {}).get(
                "analysis_number"
            ),
            "sample_taken": self._report.get("metadata", {}).get("sample_taken"),
            "tank_type": self._report.get("metadata", {}).get("tank_type"),
        }


class OceamoMeasurementSensor(OceamoBaseSensor):
    """One ICP measurement."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        entry: ConfigEntry,
        report: dict[str, Any],
        measurement: dict[str, Any],
    ) -> None:
        """Initialize a measurement sensor."""
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
        """Return numeric measurement or unknown for n.n./n.b."""
        return self._measurement.get("value")

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return Oceamo metadata for the measurement."""
        return {
            "category": self._measurement.get("category"),
            "raw_value": self._measurement.get("raw_value"),
            "detected": self._measurement.get("detected"),
            "determined": self._measurement.get("determined"),
            "target": self._measurement.get("target"),
            "status": self._measurement.get("status"),
            "analysis_number": self._report.get("metadata", {}).get(
                "analysis_number"
            ),
            "analysis_date": self._report.get("metadata", {}).get(
                "analysis_date"
            ),
        }

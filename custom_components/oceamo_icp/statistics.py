"""Historical statistics support for Reef ICP."""

from __future__ import annotations

from datetime import date, datetime, time
import re
from typing import Any

from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import CONF_REPORTS, DOMAIN


def _statistic_slug(value: str) -> str:
    """Return a Home Assistant compatible statistic-id slug."""
    value = value.lower()
    value = re.sub(r"[^a-z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_")


def statistic_id_for(entry: ConfigEntry, measurement: dict[str, Any]) -> str:
    """Return the external statistic ID for one normalized measurement."""
    entry_id = _statistic_slug(entry.entry_id)
    category = _statistic_slug(str(measurement.get("category", "unknown")))
    key = _statistic_slug(str(measurement.get("key", "unknown")))
    return f"{DOMAIN}:{entry_id}_{category}_{key}"


def _report_start(hass: HomeAssistant, report: dict[str, Any]) -> datetime | None:
    """Return an hourly, timezone-aware timestamp for the report."""
    metadata = report.get("metadata", {})
    timezone = dt_util.get_time_zone(hass.config.time_zone)

    if sample_taken := metadata.get("sample_taken"):
        try:
            start = datetime.fromisoformat(sample_taken)
        except ValueError:
            start = None
        if start is not None:
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone)
            else:
                start = start.astimezone(timezone)
            return start.replace(minute=0, second=0, microsecond=0)

    if analysis_date := metadata.get("analysis_date"):
        try:
            parsed_date = date.fromisoformat(analysis_date)
        except ValueError:
            return None
        return datetime.combine(parsed_date, time(hour=12), tzinfo=timezone)

    return None


def _statistic_name(entry: ConfigEntry, measurement: dict[str, Any]) -> str:
    """Return a human-readable statistic name."""
    name = measurement.get("name", measurement.get("key", "Measurement"))
    if measurement.get("category") == "osmosis":
        return f"{entry.title} RO/DI {name}"
    return f"{entry.title} {name}"


@callback
def async_import_icp_statistics(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Import all stored numeric ICP results into external statistics."""
    reports = list(entry.options.get(CONF_REPORTS, []))
    if not reports:
        return

    grouped: dict[str, dict[str, Any]] = {}

    for report in reports:
        start = _report_start(hass, report)
        if start is None:
            continue

        for measurement in report.get("measurements", []):
            value = measurement.get("value")
            if not isinstance(value, (int, float)):
                continue

            statistic_id = statistic_id_for(entry, measurement)
            unit = measurement.get("unit")

            bucket = grouped.setdefault(
                statistic_id,
                {
                    "metadata": StatisticMetaData(
                        source=DOMAIN,
                        statistic_id=statistic_id,
                        name=_statistic_name(entry, measurement),
                        unit_class=None,
                        unit_of_measurement=unit,
                        mean_type=StatisticMeanType.ARITHMETIC,
                        has_sum=False,
                    ),
                    "unit": unit,
                    "points": {},
                },
            )

            # Provider parsers normalize comparable analytes to one unit.
            # Never mix a point into an existing statistic if a future parser
            # accidentally supplies an incompatible unit.
            if bucket["unit"] != unit:
                continue

            numeric = float(value)
            bucket["points"][start] = StatisticData(
                start=start,
                mean=numeric,
                min=numeric,
                max=numeric,
            )

    for bucket in grouped.values():
        points = [bucket["points"][start] for start in sorted(bucket["points"])]
        if points:
            async_add_external_statistics(hass, bucket["metadata"], points)

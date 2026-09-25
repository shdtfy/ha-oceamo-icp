"""Historical statistics support for Reef ICP."""

from __future__ import annotations

import asyncio
from datetime import date, datetime, time
import logging
import re
from typing import Any, Iterable

from homeassistant.components.recorder import get_instance
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

_LOGGER = logging.getLogger(__name__)

_DATA_STATISTICS_REBUILD = "statistics_rebuild"
_STATISTICS_CLEAR_TIMEOUT = 30


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


def statistic_ids_for_reports(
    entry: ConfigEntry,
    reports: Iterable[dict[str, Any]],
) -> set[str]:
    """Return all Reef ICP statistic IDs referenced by the supplied reports."""
    return {
        statistic_id_for(entry, measurement)
        for report in reports
        for measurement in report.get("measurements", [])
    }


@callback
def async_request_statistics_rebuild(
    hass: HomeAssistant,
    entry: ConfigEntry,
    reports: Iterable[dict[str, Any]],
) -> None:
    """Request a clear-and-rebuild of statistics on the next entry reload."""
    statistic_ids = statistic_ids_for_reports(entry, reports)
    if not statistic_ids:
        return

    domain_data = hass.data.setdefault(DOMAIN, {})
    requests = domain_data.setdefault(_DATA_STATISTICS_REBUILD, {})
    pending = requests.setdefault(entry.entry_id, set())
    pending.update(statistic_ids)


@callback
def async_take_statistics_rebuild_request(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> set[str]:
    """Consume a pending statistics rebuild request for one config entry."""
    domain_data = hass.data.get(DOMAIN)
    if not isinstance(domain_data, dict):
        return set()

    requests = domain_data.get(_DATA_STATISTICS_REBUILD)
    if not isinstance(requests, dict):
        return set()

    statistic_ids = set(requests.pop(entry.entry_id, set()))
    if not requests:
        domain_data.pop(_DATA_STATISTICS_REBUILD, None)
    return statistic_ids


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


async def async_rebuild_icp_statistics(
    hass: HomeAssistant,
    entry: ConfigEntry,
    statistic_ids: set[str],
) -> None:
    """Clear stale Reef ICP statistics and rebuild them from stored reports."""
    if not statistic_ids:
        async_import_icp_statistics(hass, entry)
        return

    done_event = asyncio.Event()

    def clear_statistics_done() -> None:
        hass.loop.call_soon_threadsafe(done_event.set)

    get_instance(hass).async_clear_statistics(
        sorted(statistic_ids),
        on_done=clear_statistics_done,
    )

    try:
        async with asyncio.timeout(_STATISTICS_CLEAR_TIMEOUT):
            await done_event.wait()
    except TimeoutError:
        _LOGGER.warning(
            "Timed out while clearing Reef ICP statistics for %s; "
            "statistics will be re-imported on the next setup",
            entry.entry_id,
        )
        return

    async_import_icp_statistics(hass, entry)

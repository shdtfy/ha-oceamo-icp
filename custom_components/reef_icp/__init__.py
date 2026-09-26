"""Reef ICP integration."""

from __future__ import annotations

from pathlib import Path
import copy
from typing import Any

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA, MODE_STORAGE
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import CONF_REPORTS, DOMAIN
from .statistics import (
    async_import_icp_statistics,
    async_rebuild_icp_statistics,
    async_take_statistics_rebuild_request,
)

PLATFORMS: list[Platform] = [Platform.SENSOR]

CARD_VERSION = "0.13.6"
CARD_URL = "/reef_icp/reef-icp-card.js"
CARD_RESOURCE_URL = f"{CARD_URL}?v={CARD_VERSION}"
CARD_FILE = Path(__file__).parent / "www" / "reef-icp-card.js"
_SENSOR_PLATFORM_ENTRIES_KEY = f"{DOMAIN}_sensor_platform_entries"

_NOT_DETERMINED_RAW_VALUES = {"n.g.", "n.g", "n.b.", "n.b", "---", "-"}


def _measurement_is_determined(measurement: dict[str, Any]) -> bool:
    """Return whether a report actually determined this parameter."""
    raw = str(measurement.get("raw_value") or "").strip().lower()
    if raw in {"n.n.", "n.n"}:
        # Not detectable is still a real analytical result.
        return True
    if raw in _NOT_DETERMINED_RAW_VALUES:
        return False

    determined = measurement.get("determined")
    if determined is False:
        return False
    if determined is True:
        return True

    value = measurement.get("value")
    if value is not None:
        return True

    return bool(raw)


def _annotate_history_visibility(
    reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Mark parameters that were determined at least once in tank history."""
    updated = copy.deepcopy(reports)
    ever_determined: dict[tuple[str, str], bool] = {}

    for report in updated:
        for measurement in report.get("measurements", []):
            if not isinstance(measurement, dict):
                continue
            key = (
                str(measurement.get("category") or "unknown"),
                str(measurement.get("key") or "unknown"),
            )
            if _measurement_is_determined(measurement):
                ever_determined[key] = True
            else:
                ever_determined.setdefault(key, False)

    for report in updated:
        for measurement in report.get("measurements", []):
            if not isinstance(measurement, dict):
                continue
            key = (
                str(measurement.get("category") or "unknown"),
                str(measurement.get("key") or "unknown"),
            )
            measurement["ever_determined"] = ever_determined.get(key, False)

    return updated


async def _async_register_lovelace_resource(hass: HomeAssistant) -> None:
    """Register the bundled card as a Lovelace resource when storage mode is used."""
    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None or lovelace.resource_mode != MODE_STORAGE:
        return

    resources = lovelace.resources
    if not isinstance(resources, ResourceStorageCollection):
        return

    await resources.async_get_info()

    existing = None
    for item in resources.async_items() or []:
        url = str(item.get("url", ""))
        if url.split("?", 1)[0] == CARD_URL:
            existing = item
            break

    if existing is None:
        await resources.async_create_item(
            {
                "res_type": "module",
                "url": CARD_RESOURCE_URL,
            }
        )
        return

    if existing.get("url") != CARD_RESOURCE_URL or existing.get("type") != "module":
        await resources.async_update_item(
            existing["id"],
            {
                "res_type": "module",
                "url": CARD_RESOURCE_URL,
            },
        )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Reef ICP from YAML / frontend resources."""
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                url_path=CARD_URL,
                path=str(CARD_FILE),
                cache_headers=False,
            ),
        ]
    )

    add_extra_js_url(hass, CARD_RESOURCE_URL)
    await _async_register_lovelace_resource(hass)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Reef ICP from a config entry."""
    reports = list(entry.options.get(CONF_REPORTS, []))
    if reports:
        annotated_reports = _annotate_history_visibility(reports)
        if annotated_reports != reports:
            options = dict(entry.options)
            options[CONF_REPORTS] = annotated_reports
            hass.config_entries.async_update_entry(entry, options=options)

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        hass.data.setdefault(_SENSOR_PLATFORM_ENTRIES_KEY, set()).add(entry.entry_id)

    rebuild_ids = async_take_statistics_rebuild_request(hass, entry)
    if rebuild_ids:
        await async_rebuild_icp_statistics(hass, entry, rebuild_ids)
    else:
        async_import_icp_statistics(hass, entry)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Reef ICP config entry."""
    loaded_entries = hass.data.get(_SENSOR_PLATFORM_ENTRIES_KEY, set())
    if entry.entry_id not in loaded_entries:
        return True

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        loaded_entries.discard(entry.entry_id)
    return unloaded

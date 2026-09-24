"""Oceamo ICP integration."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA, MODE_STORAGE
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .statistics import async_import_icp_statistics

PLATFORMS: list[Platform] = [Platform.SENSOR]

CARD_VERSION = "0.3.3"
CARD_URL = "/oceamo_icp/oceamo-icp-card.js"
CARD_RESOURCE_URL = f"{CARD_URL}?v={CARD_VERSION}"
CARD_FILE = Path(__file__).parent / "www" / "oceamo-icp-card.js"


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
    """Set up the Oceamo ICP integration and bundled dashboard card."""
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                url_path=CARD_URL,
                path=str(CARD_FILE),
                cache_headers=False,
            )
        ]
    )

    add_extra_js_url(hass, CARD_RESOURCE_URL)
    await _async_register_lovelace_resource(hass)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Oceamo ICP from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async_import_icp_statistics(hass, entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an Oceamo ICP config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

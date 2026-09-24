"""Oceamo ICP integration."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .statistics import async_import_icp_statistics

PLATFORMS: list[Platform] = [Platform.SENSOR]

CARD_URL = "/oceamo_icp/oceamo-icp-card.js"
CARD_FILE = Path(__file__).parent / "www" / "oceamo-icp-card.js"


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
    add_extra_js_url(hass, CARD_URL)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Oceamo ICP from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async_import_icp_statistics(hass, entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an Oceamo ICP config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

"""Oceamo ICP integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .statistics import async_import_icp_statistics

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Oceamo ICP from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async_import_icp_statistics(hass, entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an Oceamo ICP config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

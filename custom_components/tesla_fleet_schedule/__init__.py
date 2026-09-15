"""Tesla Fleet Schedule custom integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

from .services import async_setup_services, async_unload_services


async def async_setup_entry(hass: HomeAssistant, _entry: ConfigEntry) -> bool:
    """Set up Tesla Fleet Schedule from a config entry."""
    async_setup_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, _entry: ConfigEntry) -> bool:
    """Unload Tesla Fleet Schedule services."""
    async_unload_services(hass)
    return True

"""Config flow for the Tesla Fleet Schedule integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant import config_entries

if TYPE_CHECKING:
    from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class TeslaFleetScheduleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle installation of Tesla Fleet Schedule from the UI."""

    VERSION = 1

    async def async_step_user(
        self, _user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Create the integration entry without additional configuration."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="Tesla Fleet Schedule", data={})

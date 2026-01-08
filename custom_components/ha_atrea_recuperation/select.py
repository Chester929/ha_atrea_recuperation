"""Select entity exposing the full device operation mode (holding 1001)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = "ha_atrea_recuperation"


async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    """Set up the select platform."""
    # Get data from hass.data
    hub = hass.data[DOMAIN]["hub"]
    coordinator = hass.data[DOMAIN]["coordinator"]
    name = hass.data[DOMAIN]["name"]

    # Create select entity for operation mode
    async_add_entities([OperationModeSelect(coordinator, hub, f"{name} Operation Mode")])


class OperationModeSelect(CoordinatorEntity, SelectEntity):
    """Select entity to set the device operation mode (0..8)."""

    def __init__(self, coordinator, hub, name: str) -> None:
        super().__init__(coordinator)
        self._hub = hub
        self._name = name
        self._attr_unique_id = f"ha_atrea_opmode_{name.replace(' ', '_').lower()}"

    @property
    def name(self) -> str:
        return self._name

    @property
    def current_option(self) -> str | None:
        if self.coordinator.data is None:
            return None
        val = self.coordinator.data.get(1001)
        if val is None:
            return None
        try:
            idx = int(val)
            return self.options[idx]
        except Exception:
            return None

    @property
    def options(self) -> list[str]:
        labels = []
        for i in range(0, 9):
            labels.append(self._hub._hvac_map.get(i, f"{i}"))
        return labels

    async def async_select_option(self, option: str) -> None:
        try:
            idx = self.options.index(option)
        except ValueError:
            return
        await self._hub.write_holding(1001, int(idx))
        await self.coordinator.async_request_refresh()

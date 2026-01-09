"""Select entity exposing the full device operation mode (holding 1001)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = "ha_atrea_recuperation"


async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    """Set up the select platform."""
    entities = []

    # Get all devices from hass.data
    devices = hass.data[DOMAIN].get("devices", {})

    # Create select entity for each device
    for device_key, device_data in devices.items():
        hub = device_data["hub"]
        coordinator = device_data["coordinator"]
        name = device_data["name"]

        entities.append(OperationModeSelect(coordinator, hub, f"{name} Operation Mode"))

    async_add_entities(entities)


class OperationModeSelect(CoordinatorEntity, SelectEntity):
    """Select entity to set the device operation mode (0..8)."""

    def __init__(self, coordinator, hub, name: str) -> None:
        super().__init__(coordinator)
        self._hub = hub
        self._name = name
        # Include device name in unique_id to avoid conflicts with multiple devices
        device_id = hub.name.lower().replace(" ", "_")
        self._attr_unique_id = f"ha_atrea_{device_id}_opmode"

    @property
    def name(self) -> str:
        return self._name

    @property
    def device_info(self):
        """Return device info to link this entity to the device."""
        return self._hub.device_info

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

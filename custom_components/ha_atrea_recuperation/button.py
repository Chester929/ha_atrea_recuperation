"""Button entity to pulse coils (reset actions)."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COILS

DOMAIN = "ha_atrea_recuperation"


async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    """Set up the button platform."""
    entities = []

    # Get all devices from hass.data
    devices = hass.data[DOMAIN].get("devices", {})
    
    # Create button entities for each device
    for device_key, device_data in devices.items():
        hub = device_data["hub"]
        coordinator = device_data["coordinator"]
        name = device_data["name"]

        # Buttons for coils
        for coil_addr, coil_name in COILS.items():
            entities.append(HaAtreaButton(coordinator, hub, f"{name} {coil_name}", coil_addr))

    async_add_entities(entities)


class HaAtreaButton(CoordinatorEntity, ButtonEntity):
    """Button that pulses a coil."""

    def __init__(self, coordinator, hub, name: str, coil_addr: int) -> None:
        super().__init__(coordinator)
        self._hub = hub
        self._name = name
        self._coil = int(coil_addr)
        self._attr_unique_id = f"ha_atrea_coil_{self._coil}"
        self._attr_device_info = hub.device_info

    @property
    def name(self) -> str:
        return self._name

    async def async_press(self) -> None:
        await self._hub.write_coil_pulse(self._coil, pulse_ms=500)
        await self.coordinator.async_request_refresh()

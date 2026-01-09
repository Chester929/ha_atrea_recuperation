"""Button entity to pulse coils (reset actions)."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COILS

DOMAIN = "ha_atrea_recuperation"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform from a config entry."""
    entities = []
    device_data = hass.data[DOMAIN]["devices"][entry.entry_id]
    hub = device_data["hub"]
    coordinator = device_data["coordinator"]
    name = device_data["name"]

    # Buttons for coils
    for coil_addr, coil_name in COILS.items():
        entities.append(HaAtreaButton(coordinator, hub, f"{name} {coil_name}", coil_addr))

    async_add_entities(entities)


async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    """Set up the button platform (YAML backward compatibility)."""
    entities = []

    # Get all devices from hass.data
    devices = hass.data[DOMAIN].get("devices", {})

    # Create button entities for each device (skip config entry devices)
    for device_key, device_data in devices.items():
        # Skip if this is a config entry device (has entry_id)
        if "entry_id" in device_data:
            continue
            
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
        # Include device name in unique_id to avoid conflicts with multiple devices
        device_id = hub.name.lower().replace(" ", "_")
        self._attr_unique_id = f"ha_atrea_{device_id}_coil_{self._coil}"

    @property
    def name(self) -> str:
        return self._name

    @property
    def device_info(self):
        """Return device info to link this entity to the device."""
        return self._hub.device_info

    async def async_press(self) -> None:
        await self._hub.write_coil_pulse(self._coil, pulse_ms=500)
        await self.coordinator.async_request_refresh()

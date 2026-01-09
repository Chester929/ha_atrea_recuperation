"""Fan entity (percentage) mapped to holding 1004."""

from __future__ import annotations

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = "ha_atrea_recuperation"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the fan platform from a config entry."""
    device_data = hass.data[DOMAIN]["devices"][entry.entry_id]
    hub = device_data["hub"]
    coordinator = device_data["coordinator"]
    name = device_data["name"]

    async_add_entities([HaAtreaFan(coordinator, hub, f"{name} Fan")])


async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    """Set up the fan platform (YAML backward compatibility)."""
    entities = []

    # Get all devices from hass.data
    devices = hass.data[DOMAIN].get("devices", {})

    # Create fan entity for each device (skip config entry devices)
    for device_key, device_data in devices.items():
        # Skip if this is a config entry device (has entry_id)
        if "entry_id" in device_data:
            continue
            
        hub = device_data["hub"]
        coordinator = device_data["coordinator"]
        name = device_data["name"]

        entities.append(HaAtreaFan(coordinator, hub, f"{name} Fan"))

    async_add_entities(entities)


class HaAtreaFan(CoordinatorEntity, FanEntity):
    """Percentage fan mapped to holding register 1004."""

    def __init__(self, coordinator, hub, name: str) -> None:
        super().__init__(coordinator)
        self._hub = hub
        self._name = name
        # Include device name in unique_id to avoid conflicts with multiple devices
        device_id = hub.name.lower().replace(" ", "_")
        self._attr_unique_id = f"ha_atrea_{device_id}_fan"

    @property
    def name(self) -> str:
        return self._name

    @property
    def device_info(self):
        """Return device info to link this entity to the device."""
        return self._hub.device_info

    @property
    def is_on(self) -> bool:
        if self.coordinator.data is None:
            return False
        val = self.coordinator.data.get(1004)
        if val is None:
            return False
        return int(val) > 0

    @property
    def percentage(self) -> int | None:
        if self.coordinator.data is None:
            return None
        val = self.coordinator.data.get(1004)
        if val is None:
            return None
        return int(val)

    @property
    def supported_features(self) -> int:
        return FanEntityFeature.SET_SPEED

    async def async_set_percentage(self, percentage: int) -> None:
        await self._hub.write_holding(1004, int(percentage))
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, percentage: int | None = None, **kwargs) -> None:
        if percentage is None:
            percentage = 20
        await self.async_set_percentage(int(percentage))

    async def async_turn_off(self, **kwargs) -> None:
        await self.async_set_percentage(0)

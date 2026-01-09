"""Climate entity for HA Atrea Recuperation.

- Exposes a simple climate entity that maps a subset of device modes to HA HVAC modes.
- Uses holding 1002 for target temperature, input 1104 for current temperature, holding 1001 for device mode (select).
"""

from __future__ import annotations

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = "ha_atrea_recuperation"


async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    """Set up the climate platform."""
    entities = []

    # Get all devices from hass.data
    devices = hass.data[DOMAIN].get("devices", {})

    # Create climate entity for each device
    for device_key, device_data in devices.items():
        hub = device_data["hub"]
        coordinator = device_data["coordinator"]
        name = device_data["name"]

        entities.append(HaAtreaClimate(coordinator, hub, name))

    async_add_entities(entities)


class HaAtreaClimate(CoordinatorEntity, ClimateEntity):
    """Climate entity backed by HaAtreaModbusHub and DataUpdateCoordinator."""

    def __init__(self, coordinator, hub, name: str) -> None:
        super().__init__(coordinator)
        self._hub = hub
        self._name = name
        # Include device name in unique_id to avoid conflicts with multiple devices
        device_id = hub.name.lower().replace(" ", "_")
        self._attr_unique_id = f"ha_atrea_{device_id}_climate"

    @property
    def name(self) -> str:
        return self._name

    @property
    def device_info(self):
        """Return device info to link this entity to the device."""
        return self._hub.device_info

    @property
    def temperature_unit(self) -> str:
        return self.hass.config.units.temperature_unit

    @property
    def current_temperature(self) -> float | None:
        if self.coordinator.data is None:
            return None
        val = self.coordinator.data.get(1104)
        if val is None:
            return None
        return float(val) / 10.0

    @property
    def target_temperature(self) -> float | None:
        if self.coordinator.data is None:
            return None
        val = self.coordinator.data.get(1002)
        if val is None:
            return None
        return float(val) / 10.0

    @property
    def hvac_modes(self) -> list[str]:
        return [HVACMode.OFF, HVACMode.AUTO, HVACMode.HEAT]

    @property
    def hvac_mode(self) -> str:
        if self.coordinator.data is None:
            return HVACMode.OFF
        dev_mode_val = self.coordinator.data.get(1001)
        if dev_mode_val is None:
            return HVACMode.OFF
        dev_mode = int(dev_mode_val)
        if dev_mode == 0:
            return HVACMode.OFF
        if dev_mode == 1:
            return HVACMode.AUTO
        if dev_mode in (5, 6, 7):
            return HVACMode.HEAT
        return HVACMode.AUTO

    @property
    def supported_features(self) -> int:
        return ClimateEntityFeature.TARGET_TEMPERATURE

    async def async_set_temperature(self, **kwargs):
        if ATTR_TEMPERATURE in kwargs:
            temp = kwargs[ATTR_TEMPERATURE]
            await self._hub.write_holding(1002, int(round(float(temp) * 10.0)))
            await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: str):
        inv = {
            HVACMode.OFF: 0,
            HVACMode.AUTO: 1,
            HVACMode.HEAT: 5,
        }
        val = inv.get(hvac_mode, 1)
        await self._hub.write_holding(1001, int(val))
        await self.coordinator.async_request_refresh()

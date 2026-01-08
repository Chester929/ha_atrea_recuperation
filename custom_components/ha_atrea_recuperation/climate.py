"""Climate entity for HA Atrea Recuperation.

- Exposes a simple climate entity that maps a subset of device modes to HA HVAC modes.
- Uses holding 1002 for target temperature, input 1104 for current temperature, holding 1001 for device mode (select).
"""

from __future__ import annotations

from typing import Optional

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_OFF,
    HVAC_MODE_HEAT,
    HVAC_MODE_AUTO,
    ClimateEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity


class HaAtreaClimate(CoordinatorEntity, ClimateEntity):
    """Climate entity backed by HaAtreaModbusHub and DataUpdateCoordinator."""

    def __init__(self, coordinator, hub, name: str) -> None:
        super().__init__(coordinator)
        self._hub = hub
        self._name = name
        self._attr_unique_id = f"ha_atrea_climate_{name.replace(' ', '_').lower()}"

    @property
    def name(self) -> str:
        return self._name

    @property
    def temperature_unit(self) -> str:
        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self) -> Optional[float]:
        if self.coordinator.data is None:
            return None
        val = self.coordinator.data.get(1104)
        if val is None:
            return None
        return float(val) / 10.0

    @property
    def target_temperature(self) -> Optional[float]:
        if self.coordinator.data is None:
            return None
        val = self.coordinator.data.get(1002)
        if val is None:
            return None
        return float(val) / 10.0

    @property
    def hvac_modes(self):
        return [HVAC_MODE_OFF, HVAC_MODE_AUTO, HVAC_MODE_HEAT]

    @property
    def hvac_mode(self):
        if self.coordinator.data is None:
            return HVAC_MODE_OFF
        dev_mode_val = self.coordinator.data.get(1001)
        if dev_mode_val is None:
            return HVAC_MODE_OFF
        dev_mode = int(dev_mode_val)
        if dev_mode == 0:
            return HVAC_MODE_OFF
        if dev_mode == 1:
            return HVAC_MODE_AUTO
        if dev_mode in (5, 6, 7):
            return HVAC_MODE_HEAT
        return HVAC_MODE_AUTO

    @property
    def supported_features(self) -> ClimateEntityFeature:
        return ClimateEntityFeature.TARGET_TEMPERATURE

    async def async_set_temperature(self, **kwargs):
        if ATTR_TEMPERATURE in kwargs:
            temp = kwargs[ATTR_TEMPERATURE]
            await self._hub.write_holding(1002, int(round(float(temp) * 10.0)))
            await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: str):
        inv = {
            HVAC_MODE_OFF: 0,
            HVAC_MODE_AUTO: 1,
            HVAC_MODE_HEAT: 5,
        }
        val = inv.get(hvac_mode, 1)
        await self._hub.write_holding(1001, int(val))
        await self.coordinator.async_request_refresh()

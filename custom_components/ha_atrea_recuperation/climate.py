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
)
from homeassistant.components.climate.const import SUPPORT_TARGET_TEMPERATURE
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS


class HaAtreaClimate(ClimateEntity):
    """Climate entity backed by HaAtreaModbusHub."""

    def __init__(self, hub, name: str) -> None:
        self._hub = hub
        self._name = name
        self._unique_id = f"ha_atrea_climate_{name.replace(' ', '_').lower()}"
        self._hub.subscribe(self._async_write_ha_state)

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def temperature_unit(self) -> str:
        return TEMP_CELSIUS

    @property
    def current_temperature(self) -> Optional[float]:
        val = self._hub.get_cached(1104)
        if val is None:
            return None
        return float(val) / 10.0

    @property
    def target_temperature(self) -> Optional[float]:
        val = self._hub.get_cached(1002)
        if val is None:
            return None
        return float(val) / 10.0

    @property
    def hvac_modes(self):
        return [HVAC_MODE_OFF, HVAC_MODE_AUTO, HVAC_MODE_HEAT]

    @property
    def hvac_mode(self):
        dev_mode_val = self._hub.get_cached(1001)
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
    def supported_features(self) -> int:
        return SUPPORT_TARGET_TEMPERATURE

    async def async_set_temperature(self, **kwargs):
        if ATTR_TEMPERATURE in kwargs:
            temp = kwargs[ATTR_TEMPERATURE]
            await self._hub.write_holding(1002, int(round(float(temp) * 10.0)))
            self._hub._cache[1002] = int(round(float(temp) * 10.0))
            self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: str):
        inv = {
            HVAC_MODE_OFF: 0,
            HVAC_MODE_AUTO: 1,
            HVAC_MODE_HEAT: 5,
        }
        val = inv.get(hvac_mode, 1)
        await self._hub.write_holding(1001, int(val))
        self._hub._cache[1001] = int(val)
        self.async_write_ha_state()

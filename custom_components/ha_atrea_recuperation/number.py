"""Number entity for writable holding registers (e.g., target temperature)."""

from __future__ import annotations

from typing import Optional
from homeassistant.components.number import NumberEntity


class HaAtreaNumber(NumberEntity):
    """Number entity mapping to a holding register."""

    def __init__(self, hub, name: str, register: int, scale: float = 1.0, unit: str | None = None, writable: bool = False, min_value: float | None = None, max_value: float | None = None) -> None:
        self._hub = hub
        self._name = name
        self._register = int(register)
        self._scale = float(scale)
        self._unit = unit
        self._writable = writable
        self._min = min_value
        self._max = max_value
        self._unique_id = f"ha_atrea_number_{self._register}_{name.replace(' ', '_').lower()}"
        self._hub.subscribe(self._async_write_ha_state)

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._unit

    @property
    def native_value(self) -> Optional[float]:
        v = self._hub.get_cached(self._register)
        if v is None:
            return None
        return float(v) / self._scale

    @property
    def min_value(self) -> float | None:
        return self._min

    @property
    def max_value(self) -> float | None:
        return self._max

    async def async_set_native_value(self, value: float) -> None:
        raw = int(round(float(value) * self._scale))
        await self._hub.write_holding(self._register, raw)
        self._hub._cache[self._register] = raw
        self.async_write_ha_state()

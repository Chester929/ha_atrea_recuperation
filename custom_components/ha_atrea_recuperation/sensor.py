"""Generic sensor entity for HA Atrea Recuperation reading cached registers.

Sensors read values from hub cache. Some sensors combine register pairs (32-bit)
or build a serial string from character registers.
"""

from __future__ import annotations

from typing import Optional
from homeassistant.components.sensor import SensorEntity

class HaAtreaSensor(SensorEntity):
    """Sensor reading a single register (or combined pair) from the hub cache."""

    def __init__(self, hub, name: str, register: int, scale: float = 1.0, unit: str | None = None, holding: bool = False) -> None:
        self._hub = hub
        self._name = name
        self._register = int(register)
        self._scale = float(scale)
        self._unit = unit
        self._holding = holding
        self._unique_id = f"ha_atrea_sensor_{self._register}_{name.replace(' ', '_').lower()}"
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
        # 32-bit counters (combine low + high)
        if self._register in (3200, 3202, 3204):
            low = self._hub.get_cached(self._register)
            high = self._hub.get_cached(self._register + 1)
            if low is None:
                return None
            if high is None:
                return float(low)
            val32 = int(low) + (int(high) << 16)
            return float(val32)
        # Serial number - combine chars 3000..3008 when sensor for 3000 is used
        if self._register == 3000:
            chars = []
            for r in range(3000, 3009):
                v = self._hub.get_cached(r)
                if v is None:
                    continue
                try:
                    chars.append(chr(int(v)))
                except Exception:
                    chars.append("?")
            if not chars:
                return None
            return "".join(chars)
        # Regular single-register sensor
        v = self._hub.get_cached(self._register)
        if v is None:
            return None
        try:
            return float(v) / self._scale
        except Exception:
            return None

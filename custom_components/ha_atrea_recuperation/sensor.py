"""Generic sensor entity for HA Atrea Recuperation reading cached registers.

Sensors read values from hub cache. Some sensors combine register pairs (32-bit)
or build a serial string from character registers.
"""

from __future__ import annotations

from typing import Optional
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity


class HaAtreaSensor(CoordinatorEntity, SensorEntity):
    """Sensor reading a single register (or combined pair) from the coordinator data."""

    def __init__(
        self,
        coordinator,
        hub,
        name: str,
        register: int,
        scale: float = 1.0,
        unit: str | None = None,
        holding: bool = False
    ) -> None:
        super().__init__(coordinator)
        self._name = name
        self._register = int(register)
        self._scale = float(scale)
        self._unit = unit
        self._holding = holding
        self._attr_unique_id = f"ha_atrea_sensor_{self._register}_{name.replace(' ', '_').lower()}"

    @property
    def name(self) -> str:
        return self._name

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._unit

    @property
    def native_value(self) -> Optional[float]:
        if self.coordinator.data is None:
            return None
        # 32-bit counters (combine low + high)
        if self._register in (3200, 3202, 3204):
            low = self.coordinator.data.get(self._register)
            high = self.coordinator.data.get(self._register + 1)
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
                v = self.coordinator.data.get(r)
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
        v = self.coordinator.data.get(self._register)
        if v is None:
            return None
        try:
            return float(v) / self._scale
        except Exception:
            return None

"""Generic sensor entity for HA Atrea Recuperation reading cached registers.

Sensors read values from coordinator data. Some sensors combine register pairs (32-bit)
or build a serial string from character registers.
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import HOLDING_REGISTERS, INPUT_REGISTERS

DOMAIN = "ha_atrea_recuperation"


async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    entities = []

    # Get all devices from hass.data
    devices = hass.data[DOMAIN].get("devices", {})

    # Create entities for each device
    for device_key, device_data in devices.items():
        hub = device_data["hub"]
        coordinator = device_data["coordinator"]
        name = device_data["name"]

        # Sensors from INPUT_REGISTERS
        for reg, meta in INPUT_REGISTERS.items():
            entities.append(
                HaAtreaSensor(
                    coordinator,
                    hub,
                    f"{name} {meta['name']}",
                    reg,
                    scale=meta.get("scale", 1.0),
                    unit=meta.get("unit"),
                )
            )

        # Sensors from HOLDING_REGISTERS (expose read-only)
        for reg, meta in HOLDING_REGISTERS.items():
            entities.append(
                HaAtreaSensor(
                    coordinator,
                    hub,
                    f"{name} {meta['name']}",
                    reg,
                    scale=meta.get("scale", 1.0),
                    unit=meta.get("unit"),
                    holding=True,
                )
            )

    async_add_entities(entities)


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
        self._hub = hub
        self._name = name
        self._register = int(register)
        self._scale = float(scale)
        self._unit = unit
        self._holding = holding
        # Include device name in unique_id to avoid conflicts with multiple devices
        device_id = hub.name.lower().replace(" ", "_")
        self._attr_unique_id = f"ha_atrea_{device_id}_sensor_{self._register}_{name.replace(' ', '_').lower()}"

    @property
    def name(self) -> str:
        return self._name

    @property
    def device_info(self):
        """Return device info to link this entity to the device."""
        return self._hub.device_info

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._unit

    @property
    def native_value(self) -> float | str | None:
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

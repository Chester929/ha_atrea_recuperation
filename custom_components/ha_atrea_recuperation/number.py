"""Number entity for writable holding registers (e.g., target temperature)."""

from __future__ import annotations

from typing import Optional

from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import HOLDING_REGISTERS

DOMAIN = "ha_atrea_recuperation"


async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    """Set up the number platform."""
    entities = []

    # Get all devices from hass.data
    devices = hass.data[DOMAIN].get("devices", {})

    # Create number entity for each device
    for device_key, device_data in devices.items():
        hub = device_data["hub"]
        coordinator = device_data["coordinator"]
        name = device_data["name"]

        entities.append(
            HaAtreaNumber(
                coordinator,
                hub,
                f"{name} Target Temperature",
                1002,
                scale=HOLDING_REGISTERS[1002]["scale"],
                unit=HOLDING_REGISTERS[1002]["unit"],
                writable=True,
                min_value=-30.0,
                max_value=90.0,
            )
        )

    async_add_entities(entities)


class HaAtreaNumber(CoordinatorEntity, NumberEntity):
    """Number entity mapping to a holding register."""

    def __init__(
        self,
        coordinator,
        hub,
        name: str,
        register: int,
        scale: float = 1.0,
        unit: str | None = None,
        writable: bool = False,
        min_value: float | None = None,
        max_value: float | None = None
    ) -> None:
        super().__init__(coordinator)
        self._hub = hub
        self._name = name
        self._register = int(register)
        self._scale = float(scale)
        self._unit = unit
        self._writable = writable
        self._min = min_value
        self._max = max_value
        # Include device name in unique_id to avoid conflicts with multiple devices
        device_id = hub.name.lower().replace(" ", "_")
        self._attr_unique_id = f"ha_atrea_{device_id}_number_{self._register}"

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
    def native_value(self) -> Optional[float]:
        if self.coordinator.data is None:
            return None
        v = self.coordinator.data.get(self._register)
        if v is None:
            return None
        return float(v) / self._scale

    @property
    def native_min_value(self) -> float:
        return self._min if self._min is not None else 0.0

    @property
    def native_max_value(self) -> float:
        return self._max if self._max is not None else 100.0

    async def async_set_native_value(self, value: float) -> None:
        raw = int(round(float(value) * self._scale))
        await self._hub.write_holding(self._register, raw)
        await self.coordinator.async_request_refresh()

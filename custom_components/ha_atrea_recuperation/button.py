"""Button entity to pulse coils (reset actions)."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity


class HaAtreaButton(CoordinatorEntity, ButtonEntity):
    """Button that pulses a coil."""

    def __init__(self, coordinator, hub, name: str, coil_addr: int) -> None:
        super().__init__(coordinator)
        self._hub = hub
        self._name = name
        self._coil = int(coil_addr)
        self._attr_unique_id = f"ha_atrea_coil_{self._coil}"

    @property
    def name(self) -> str:
        return self._name

    async def async_press(self) -> None:
        await self._hub.write_coil_pulse(self._coil, pulse_ms=500)
        await self.coordinator.async_request_refresh()

"""Button entity to pulse coils (reset actions)."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity

class HaAtreaButton(ButtonEntity):
    """Button that pulses a coil."""

    def __init__(self, hub, name: str, coil_addr: int) -> None:
        self._hub = hub
        self._name = name
        self._coil = int(coil_addr)
        self._unique_id = f"ha_atrea_coil_{self._coil}"

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    async def async_press(self) -> None:
        await self._hub.write_coil_pulse(self._coil, pulse_ms=500)

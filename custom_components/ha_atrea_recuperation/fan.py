"""Fan entity (percentage) mapped to holding 1004."""

from __future__ import annotations

from homeassistant.components.fan import FanEntity, SUPPORT_SET_SPEED

class HaAtreaFan(FanEntity):
    """Percentage fan mapped to holding register 1004."""

    def __init__(self, hub, name: str) -> None:
        self._hub = hub
        self._name = name
        self._unique_id = f"ha_atrea_fan_{name.replace(' ', '_').lower()}"
        self._hub.subscribe(self._async_write_ha_state)

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def is_on(self) -> bool:
        val = self._hub.get_cached(1004)
        if val is None:
            return False
        return int(val) > 0

    @property
    def percentage(self) -> int | None:
        val = self._hub.get_cached(1004)
        if val is None:
            return None
        return int(val)

    @property
    def supported_features(self) -> int:
        return SUPPORT_SET_SPEED

    async def async_set_percentage(self, percentage: int) -> None:
        await self._hub.write_holding(1004, int(percentage))
        self._hub._cache[1004] = int(percentage)
        self.async_write_ha_state()

    async def async_turn_on(self, percentage: int | None = None, **kwargs) -> None:
        if percentage is None:
            percentage = 20
        await self.async_set_percentage(int(percentage))

    async def async_turn_off(self, **kwargs) -> None:
        await self.async_set_percentage(0)

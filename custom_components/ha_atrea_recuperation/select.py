"""Select entity exposing the full device operation mode (holding 1001)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity


class OperationModeSelect(SelectEntity):
    """Select entity to set the device operation mode (0..8)."""

    def __init__(self, hub, name: str) -> None:
        self._hub = hub
        self._name = name
        self._unique_id = f"ha_atrea_opmode_{name.replace(' ', '_').lower()}"
        self._hub.subscribe(self._async_write_ha_state)

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def current_option(self) -> str | None:
        val = self._hub.get_cached(1001)
        if val is None:
            return None
        try:
            idx = int(val)
            return self.options[idx]
        except Exception:
            return None

    @property
    def options(self) -> list[str]:
        labels = []
        for i in range(0, 9):
            labels.append(self._hub._hvac_map.get(i, f"{i}"))
        return labels

    async def async_select_option(self, option: str) -> None:
        try:
            idx = self.options.index(option)
        except ValueError:
            return
        await self._hub.write_holding(1001, int(idx))
        self._hub._cache[1001] = int(idx)
        self.async_write_ha_state()

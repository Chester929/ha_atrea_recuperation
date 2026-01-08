"""Hub that manages Modbus I/O for HA Atrea Recuperation.

- Uses Home Assistant Modbus integration hub when configured (recommended).
- Falls back to pymodbus ModbusTcpClient for direct TCP access when HA Modbus hub is not available.
- Polls input registers and holdings, caches values and notifies subscribers.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)

DEFAULT_HVAC_MAP = {
    0: "Off",
    1: "Auto",
    2: "Ventilation",
    3: "Circulation with ventilation",
    4: "Circulation",
    5: "Night precooling",
    6: "Balancing",
    7: "Overpressure",
    8: "Undefined",
}


class HaAtreaModbusHub:
    """Hub to read/write registers and cache values."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        host: Optional[str] = None,
        port: int = 502,
        unit: int = 1,
        modbus_hub_name: Optional[str] = None,
        poll_interval: int = 10,
        hvac_map: Dict[int, str] | None = None,
    ) -> None:
        self.hass = hass
        self.name = name
        self.host = host
        self.port = int(port)
        self.unit = int(unit)
        self.modbus_hub_name = modbus_hub_name
        self.poll_interval = timedelta(seconds=int(poll_interval))
        self._hvac_map = hvac_map or DEFAULT_HVAC_MAP

        # cache for registers
        self._cache: Dict[int, Any] = {}
        self._subs: List[Callable] = []

        # try to find HA modbus hub if provided
        self._ha_modbus_hub = None
        if self.modbus_hub_name:
            try:
                self._ha_modbus_hub = self.hass.data.get("modbus", {}).get(self.modbus_hub_name)
            except Exception:
                self._ha_modbus_hub = None

    def subscribe(self, callback: Callable) -> None:
        if callback not in self._subs:
            self._subs.append(callback)

    def _notify(self) -> None:
        for cb in list(self._subs):
            try:
                cb()
            except Exception:
                _LOGGER.exception("Error notifying subscriber")

    async def async_start(self) -> None:
        """Start polling loop."""
        async_track_time_interval(self.hass, self._async_poll, self.poll_interval)
        await self._async_poll(None)

    async def _async_poll(self, now) -> None:
        """Poll a set of registers and update cache.

        The list below reflects the input and holding registers present in the document.
        """
        try:
            registers_to_poll = [
                # inputs
                1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014,
                1101, 1102, 1103, 1104, 1105, 1106, 1107, 1108, 1109, 1110, 1111, 1112, 1113, 1114,
                1201, 1202, 1203, 1204, 1205, 1206,
                3000, 3001, 3002, 3003, 3004, 3005, 3006, 3007, 3008,
                3100, 3101, 3102, 3103,
                3200, 3201, 3202, 3203, 3204, 3205,
                7103, 7104, 7105,
                # holdings (we read a selected set here)
                1001, 1002, 1003, 1004, 1005, 1006, 1500, 1501, 3189, 3190,
            ]
            for reg in registers_to_poll:
                val = await self._read_register(reg)
                if val is not None:
                    self._cache[int(reg)] = val
            self._notify()
        except Exception:
            _LOGGER.exception("Error in polling loop")

    async def _read_register(self, address: int) -> Any:
        """Read a single register using the HA Modbus hub if available, else pymodbus fallback."""
        try:
            # Prefer HA Modbus hub
            if self._ha_modbus_hub:
                # try read_input_registers
                if hasattr(self._ha_modbus_hub, "read_input_registers"):
                    try:
                        result = await self.hass.async_add_executor_job(
                            self._ha_modbus_hub.read_input_registers, address, 1, self.unit
                        )
                        if result is not None:
                            if hasattr(result, "registers"):
                                return result.registers[0]
                            if isinstance(result, (list, tuple)):
                                return result[0]
                    except Exception:
                        pass
                # try read_holding_registers
                if hasattr(self._ha_modbus_hub, "read_holding_registers"):
                    try:
                        result = await self.hass.async_add_executor_job(
                            self._ha_modbus_hub.read_holding_registers, address, 1, self.unit
                        )
                        if result is not None:
                            if hasattr(result, "registers"):
                                return result.registers[0]
                            if isinstance(result, (list, tuple)):
                                return result[0]
                    except Exception:
                        pass

            # Fallback to direct pymodbus read
            if not self.host:
                return None
            return await self.hass.async_add_executor_job(_pymodbus_read_best_effort, self.host, self.port, self.unit, int(address))
        except Exception:
            _LOGGER.exception("Error reading register %s", address)
            return None

    async def write_holding(self, address: int, value: int) -> bool:
        """Write a single holding register via HA modbus hub if available, or pymodbus fallback."""
        try:
            # Try HA Modbus hub first
            if self._ha_modbus_hub and hasattr(self._ha_modbus_hub, "write_register"):
                ok = await self.hass.async_add_executor_job(self._ha_modbus_hub.write_register, address, int(value), self.unit)
                if ok:
                    return True
            # Fallback to pymodbus
            if not self.host:
                _LOGGER.error("No host configured for pymodbus fallback")
                return False
            ok = await self.hass.async_add_executor_job(_pymodbus_write_register, self.host, self.port, self.unit, int(address), int(value))
            return bool(ok)
        except Exception:
            _LOGGER.exception("Error writing holding register %s", address)
            return False

    async def write_coil_pulse(self, coil_addr: int, pulse_ms: int = 500) -> None:
        """Pulse a coil (True -> wait -> False) using HA modbus hub or pymodbus fallback."""
        try:
            if self._ha_modbus_hub and hasattr(self._ha_modbus_hub, "write_coil"):
                await self.hass.async_add_executor_job(self._ha_modbus_hub.write_coil, coil_addr, True, self.unit)
                await self.hass.async_add_executor_job(self._sleep_ms, pulse_ms)
                await self.hass.async_add_executor_job(self._ha_modbus_hub.write_coil, coil_addr, False, self.unit)
                return
            if not self.host:
                _LOGGER.error("No host configured for pymodbus fallback")
                return
            await self.hass.async_add_executor_job(_pymodbus_pulse_coil, self.host, self.port, self.unit, int(coil_addr), int(pulse_ms))
        except Exception:
            _LOGGER.exception("Error pulsing coil %s", coil_addr)

    def get_cached(self, address: int) -> Any:
        """Return cached value for a register, or None."""
        return self._cache.get(int(address))

    @staticmethod
    def _sleep_ms(ms: int) -> None:
        import time
        time.sleep(ms / 1000.0)


# -------------------------
# pymodbus helper functions (blocking; run in executor)
# -------------------------
def _pymodbus_read_best_effort(host: str, port: int, unit: int, address: int):
    """Try reading as input, then holding, return first successful integer register."""
    try:
        from pymodbus.client.sync import ModbusTcpClient
    except Exception:
        _LOGGER.exception("pymodbus not available")
        return None
    client = ModbusTcpClient(host=host, port=port)
    try:
        if not client.connect():
            _LOGGER.debug("Cannot connect to pymodbus %s:%s", host, port)
            return None
        # try input registers
        rr = client.read_input_registers(address, count=1, unit=unit)
        if rr and (not hasattr(rr, "isError") or not rr.isError()):
            if hasattr(rr, "registers"):
                return rr.registers[0]
            if isinstance(rr, (list, tuple)):
                return rr[0]
        # try holding registers
        rr = client.read_holding_registers(address, count=1, unit=unit)
        if rr and (not hasattr(rr, "isError") or not rr.isError()):
            if hasattr(rr, "registers"):
                return rr.registers[0]
            if isinstance(rr, (list, tuple)):
                return rr[0]
        return None
    except Exception:
        _LOGGER.exception("pymodbus read error at %s", address)
        return None
    finally:
        try:
            client.close()
        except Exception:
            pass


def _pymodbus_write_register(host: str, port: int, unit: int, address: int, value: int) -> bool:
    try:
        from pymodbus.client.sync import ModbusTcpClient
    except Exception:
        _LOGGER.exception("pymodbus not available")
        return False
    client = ModbusTcpClient(host=host, port=port)
    try:
        if not client.connect():
            _LOGGER.debug("Cannot connect to pymodbus %s:%s", host, port)
            return False
        rr = client.write_register(address, int(value), unit=unit)
        if rr and (not hasattr(rr, "isError") or not rr.isError()):
            return True
        return False
    except Exception:
        _LOGGER.exception("pymodbus write error at %s", address)
        return False
    finally:
        try:
            client.close()
        except Exception:
            pass


def _pymodbus_pulse_coil(host: str, port: int, unit: int, coil_addr: int, ms: int) -> None:
    try:
        from pymodbus.client.sync import ModbusTcpClient
    except Exception:
        _LOGGER.exception("pymodbus not available")
        return False
    import time
    client = ModbusTcpClient(host=host, port=port)
    try:
        if not client.connect():
            _LOGGER.debug("Cannot connect to pymodbus %s:%s", host, port)
            return False
        client.write_coil(coil_addr, True, unit=unit)
        time.sleep(ms / 1000.0)
        client.write_coil(coil_addr, False, unit=unit)
        return True
    except Exception:
        _LOGGER.exception("pymodbus coil error at %s", coil_addr)
        return False
    finally:
        try:
            client.close()
        except Exception:
            pass

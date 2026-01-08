"""Hub that manages Modbus I/O for HA Atrea Recuperation.

- Uses Home Assistant Modbus integration hub when configured (recommended).
- Falls back to pymodbus ModbusTcpClient for direct TCP access when HA Modbus hub is not available.
- Polls input registers and holdings, caches values and notifies subscribers.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant

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

        # HA modbus hub will be retrieved lazily when needed
        self._ha_modbus_hub = None

    def _get_ha_modbus_hub(self):
        """Get the HA Modbus hub from hass.data if available.

        This attempts multiple strategies:
        - If hass.data['modbus'] is a dict and a name is configured, use it.
        - Otherwise scan hass.data['modbus'] for a hub object with async_pb_call.
        - As a last resort scan top-level hass.data values for an object with async_pb_call.
        """
        if self._ha_modbus_hub is None:
            try:
                modbus_hubs = self.hass.data.get("modbus")
                if isinstance(modbus_hubs, dict):
                    if self.modbus_hub_name:
                        hub = modbus_hubs.get(self.modbus_hub_name)
                        if hub and hasattr(hub, "async_pb_call"):
                            self._ha_modbus_hub = hub
                            _LOGGER.debug("Found HA Modbus hub by name: %s", self.modbus_hub_name)
                            return self._ha_modbus_hub
                    # scan the dict for a candidate
                    for k, v in modbus_hubs.items():
                        if hasattr(v, "async_pb_call"):
                            self._ha_modbus_hub = v
                            _LOGGER.debug("Found HA Modbus hub by scanning modbus dict: %s", k)
                            return self._ha_modbus_hub

                # fallback: scan top-level hass.data for an object exposing async_pb_call
                for k, v in self.hass.data.items():
                    if hasattr(v, "async_pb_call"):
                        self._ha_modbus_hub = v
                        _LOGGER.debug("Found HA Modbus hub in hass.data key: %s", k)
                        return self._ha_modbus_hub

            except Exception as ex:
                _LOGGER.debug("Could not get HA Modbus hub: %s", ex)
        return self._ha_modbus_hub

    async def async_update(self) -> Dict[int, Any]:
        """Poll a set of registers and update cache.

        The list below reflects the input and holding registers present in the document.
        This method is called by DataUpdateCoordinator.
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
                    _LOGGER.debug("Cached register %s = %s", reg, val)
                else:
                    _LOGGER.debug("No value for register %s", reg)
            return self._cache
        except Exception:
            _LOGGER.exception("Error in polling loop")
            return self._cache

    async def _read_register(self, address: int) -> Any:
        """Read a single register using the HA Modbus hub if available, else pymodbus fallback."""
        try:
            # Prefer HA Modbus hub
            ha_hub = self._get_ha_modbus_hub()
            if ha_hub and hasattr(ha_hub, "async_pb_call"):
                _LOGGER.debug("Using HA Modbus hub for address %s (unit=%s)", address, self.unit)
                # Try reading as input register first
                try:
                    result = await ha_hub.async_pb_call(
                        self.unit, address, 1, "read_input_registers"
                    )
                    _LOGGER.debug("HA hub read_input_registers result for %s: %s", address, getattr(result, "registers", result))
                    if result and hasattr(result, "registers") and result.registers:
                        return result.registers[0]
                except Exception as ex:
                    _LOGGER.debug("HA hub read_input_registers failed for %s: %s", address, ex)

                # Try reading as holding register
                try:
                    result = await ha_hub.async_pb_call(
                        self.unit, address, 1, "read_holding_registers"
                    )
                    _LOGGER.debug("HA hub read_holding_registers result for %s: %s", address, getattr(result, "registers", result))
                    if result and hasattr(result, "registers") and result.registers:
                        return result.registers[0]
                except Exception as ex:
                    _LOGGER.debug("HA hub read_holding_registers failed for %s: %s", address, ex)

            # Fallback to direct pymodbus read
            if not self.host:
                _LOGGER.debug("No host configured for pymodbus fallback (address %s)", address)
                return None
            _LOGGER.debug("Using pymodbus fallback to read address %s on %s:%s", address, self.host, self.port)
            return await self.hass.async_add_executor_job(_pymodbus_read_best_effort, self.host, self.port, self.unit, int(address))
        except Exception:
            _LOGGER.exception("Error reading register %s", address)
            return None

    async def write_holding(self, address: int, value: int) -> bool:
        """Write a single holding register via HA modbus hub if available, or pymodbus fallback."""
        try:
            # Try HA Modbus hub first
            ha_hub = self._get_ha_modbus_hub()
            if ha_hub and hasattr(ha_hub, "async_pb_call"):
                result = await ha_hub.async_pb_call(
                    self.unit, address, int(value), "write_register"
                )
                _LOGGER.debug("HA hub write_register result for %s: %s", address, result)
                if result:
                    # Update cache immediately for optimistic updates
                    self._cache[int(address)] = int(value)
                    return True

            # Fallback to pymodbus
            if not self.host:
                _LOGGER.error("No host configured for pymodbus fallback")
                return False
            ok = await self.hass.async_add_executor_job(_pymodbus_write_register, self.host, self.port, self.unit, int(address), int(value))
            if ok:
                # Update cache immediately for optimistic updates
                self._cache[int(address)] = int(value)
            return bool(ok)
        except Exception:
            _LOGGER.exception("Error writing holding register %s", address)
            return False

    async def write_coil_pulse(self, coil_addr: int, pulse_ms: int = 500) -> None:
        """Pulse a coil (True -> wait -> False) using HA modbus hub or pymodbus fallback."""
        try:
            ha_hub = self._get_ha_modbus_hub()
            if ha_hub and hasattr(ha_hub, "async_pb_call"):
                # Write True
                await ha_hub.async_pb_call(self.unit, coil_addr, True, "write_coil")
                # Wait
                await self.hass.async_add_executor_job(self._sleep_ms, pulse_ms)
                # Write False
                await ha_hub.async_pb_call(self.unit, coil_addr, False, "write_coil")
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

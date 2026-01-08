"""HA Atrea Recuperation integration (YAML-configured).

This integration expects you to configure the Home Assistant Modbus integration and
set `modbus_hub` to the name of that hub. It exposes:
- climate: target temperature + simplified HVAC mapping
- select: full device operation mode (writes to holding 1001)
- fan: percentage control (writes to holding 1004)
- number: target temperature (holding 1002)
- sensors: input and holding registers from the device doc
- buttons: coil actions (7001, 8000, 8001, 8002)
"""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.entity_component import EntityComponent

from .hub import HaAtreaModbusHub
from .climate import HaAtreaClimate
from .select import OperationModeSelect
from .fan import HaAtreaFan
from .number import HaAtreaNumber
from .sensor import HaAtreaSensor
from .button import HaAtreaButton

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ha_atrea_recuperation"
DEFAULT_NAME = "HA Atrea Recuperation"

# Input registers (read-only) with scale and unit (subset shown; hub polls a larger list)
INPUT_REGISTERS = {
    1001: {"name": "Mode (input)", "scale": 1, "unit": None},
    1002: {"name": "Desired temperature (input)", "scale": 10, "unit": "°C"},
    1101: {"name": "Outdoor temperature", "scale": 10, "unit": "°C"},
    1102: {"name": "Supply temperature", "scale": 10, "unit": "°C"},
    1103: {"name": "Extract temperature", "scale": 10, "unit": "°C"},
    1104: {"name": "Indoor temperature", "scale": 10, "unit": "°C"},
    1105: {"name": "Return temperature", "scale": 10, "unit": "°C"},
    1107: {"name": "Supply fan power", "scale": 1, "unit": "%"},
    1108: {"name": "Extract fan power", "scale": 1, "unit": "%"},
    1109: {"name": "Supply flow", "scale": 0.1, "unit": "m³/h"},
    1110: {"name": "Extract flow", "scale": 0.1, "unit": "m³/h"},
    1111: {"name": "Fresh air flow", "scale": 0.1, "unit": "m³/h"},
    # serial chars and hour counters will be decoded by the hub/sensor
    3000: {"name": "SN char 1", "scale": 1, "unit": None},
    3001: {"name": "SN char 2", "scale": 1, "unit": None},
    3002: {"name": "SN char 3", "scale": 1, "unit": None},
    3003: {"name": "SN char 4", "scale": 1, "unit": None},
    3004: {"name": "SN char 5", "scale": 1, "unit": None},
    3005: {"name": "SN char 6", "scale": 1, "unit": None},
    3006: {"name": "SN char 7", "scale": 1, "unit": None},
    3007: {"name": "SN char 8", "scale": 1, "unit": None},
    3008: {"name": "SN char 9", "scale": 1, "unit": None},
    3200: {"name": "M1 hours (low)", "scale": 1, "unit": "h"},
    3201: {"name": "M1 hours (high)", "scale": 1, "unit": None},
    3202: {"name": "M2 hours (low)", "scale": 1, "unit": "h"},
    3203: {"name": "M2 hours (high)", "scale": 1, "unit": None},
    3204: {"name": "UV hours (low)", "scale": 1, "unit": "h"},
    3205: {"name": "UV hours (high)", "scale": 1, "unit": None},
    7103: {"name": "Trigger WC+upper bath", "scale": 1, "unit": None},
    7104: {"name": "Trigger WC+lower bath", "scale": 1, "unit": None},
    7105: {"name": "Trigger technical room", "scale": 1, "unit": None},
}

# Holding registers (read/write where appropriate)
HOLDING_REGISTERS = {
    1001: {"name": "Mode (holding)", "scale": 1, "unit": None},
    1002: {"name": "Desired temperature (holding)", "scale": 10, "unit": "°C"},
    1003: {"name": "Selected zone (holding)", "scale": 1, "unit": None},
    1004: {"name": "Desired power (holding)", "scale": 1, "unit": "%"},
    1005: {"name": "Desired ventilation power", "scale": 0.1, "unit": "m³/h"},
    1006: {"name": "Desired supply power", "scale": 0.1, "unit": "m³/h"},
    1500: {"name": "Indoor temperature (holding)", "scale": 10, "unit": "°C"},
    1501: {"name": "Outdoor temperature (holding)", "scale": 10, "unit": "°C"},
    3189: {"name": "Active calendar", "scale": 1, "unit": None},
    3190: {"name": "Active scene", "scale": 1, "unit": None},
}

COILS = {
    7001: "Example function",
    8000: "reset_states",
    8001: "reset_filters",
    8002: "reset_uv",
}


async def async_setup(hass: HomeAssistant, config: dict):
    """YAML setup entrypoint for the custom component."""
    conf = config.get(DOMAIN)
    if conf is None:
        _LOGGER.error("No configuration found for %s", DOMAIN)
        return True

    name = conf.get("name", DEFAULT_NAME)
    modbus_hub = conf.get("modbus_hub")  # name of HA modbus hub to reuse (recommended)
    host = conf.get("modbus_host")  # fallback host if no HA modbus hub is used
    port = int(conf.get("modbus_port", 502))
    unit = int(conf.get("unit", 1))
    poll = int(conf.get("poll_interval", 10))
    hvac_map = conf.get("hvac_mode_labels", None)

    hub = HaAtreaModbusHub(
        hass,
        name,
        host=host,
        port=port,
        unit=unit,
        modbus_hub_name=modbus_hub,
        poll_interval=poll,
        hvac_map=hvac_map,
    )

    # Create DataUpdateCoordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{name}",
        update_method=hub.async_update,
        update_interval=timedelta(seconds=poll),
    )

    # Perform initial refresh suitable for YAML-based integration
    await coordinator.async_refresh()

    entities = []

    # Climate
    entities.append(HaAtreaClimate(coordinator, hub, name))

    # Operation mode select (writes to holding 1001)
    entities.append(OperationModeSelect(coordinator, hub, f"{name} Operation Mode"))

    # Fan entity controlling holding 1004 (percentage)
    entities.append(HaAtreaFan(coordinator, hub, f"{name} Fan"))

    # Number - target temperature (holding 1002)
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

    # Sensors from INPUT_REGISTERS
    for reg, meta in INPUT_REGISTERS.items():
        entities.append(HaAtreaSensor(coordinator, hub, f"{name} {meta['name']}", reg, scale=meta.get("scale", 1.0), unit=meta.get("unit")))

    # Sensors from HOLDING_REGISTERS (expose read-only)
    for reg, meta in HOLDING_REGISTERS.items():
        entities.append(HaAtreaSensor(coordinator, hub, f"{name} {meta['name']}", reg, scale=meta.get("scale", 1.0), unit=meta.get("unit"), holding=True))

    # Buttons for coils
    for coil_addr, coil_name in COILS.items():
        entities.append(HaAtreaButton(coordinator, hub, f"{name} {coil_name}", coil_addr))

    # register hub and coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["hub"] = hub
    hass.data[DOMAIN]["coordinator"] = coordinator

    # Use an EntityComponent to add entities (compatible with HA core patterns)
    component = EntityComponent(hass, _LOGGER, DOMAIN)
    await component.async_add_entities(entities)

    _LOGGER.info("HA Atrea Recuperation integration initialized")
    return True

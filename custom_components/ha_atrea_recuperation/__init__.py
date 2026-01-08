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
from homeassistant.helpers import discovery
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .hub import HaAtreaModbusHub

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ha_atrea_recuperation"
DEFAULT_NAME = "HA Atrea Recuperation"


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

    # Store hub and coordinator in hass.data for platforms to access
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["hub"] = hub
    hass.data[DOMAIN]["coordinator"] = coordinator
    hass.data[DOMAIN]["name"] = name
    hass.data[DOMAIN]["config"] = conf

    # Load platforms using discovery helper
    for platform in ("climate", "sensor", "select", "fan", "number", "button"):
        hass.async_create_task(
            discovery.async_load_platform(
                hass,
                platform,
                DOMAIN,
                {},
                config,
            )
        )

    _LOGGER.info("HA Atrea Recuperation integration initialized")
    return True

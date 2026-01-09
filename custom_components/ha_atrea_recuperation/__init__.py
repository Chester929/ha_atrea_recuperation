"""HA Atrea Recuperation integration.

This integration supports both:
1. YAML configuration (legacy, backward compatible)
2. UI configuration via config flow (new, recommended)

Exposes:
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

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    CONF_MODBUS_HUB,
    CONF_UNIT,
    CONF_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
)
from .hub import HaAtreaModbusHub

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.FAN,
    Platform.NUMBER,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA Atrea Recuperation from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("devices", {})

    # Extract configuration from entry
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    modbus_hub = entry.data.get(CONF_MODBUS_HUB)
    host = entry.data.get(CONF_HOST)
    port = entry.data.get(CONF_PORT, 502)
    unit = entry.data.get(CONF_UNIT, 1)
    
    # Check for poll_interval in options first, then data
    poll_interval = entry.options.get(
        CONF_POLL_INTERVAL,
        entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
    )

    # Create hub
    hub = HaAtreaModbusHub(
        hass,
        name,
        host=host,
        port=port,
        unit=unit,
        modbus_hub_name=modbus_hub,
        poll_interval=poll_interval,
        hvac_map=None,  # Use default
    )

    # Create DataUpdateCoordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{name}",
        update_method=hub.async_update,
        update_interval=timedelta(seconds=poll_interval),
    )

    # Perform initial refresh
    await coordinator.async_config_entry_first_refresh()

    # Store hub and coordinator
    device_key = entry.entry_id
    hass.data[DOMAIN]["devices"][device_key] = {
        "hub": hub,
        "coordinator": coordinator,
        "name": name,
        "config": entry.data,
        "entry_id": entry.entry_id,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    _LOGGER.info("HA Atrea Recuperation device '%s' initialized from config entry", name)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Remove device data
        device_key = entry.entry_id
        hass.data[DOMAIN]["devices"].pop(device_key, None)
        _LOGGER.info("HA Atrea Recuperation device unloaded")

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup(hass: HomeAssistant, config: dict):
    """YAML setup entrypoint for the custom component (backward compatibility)."""
    conf = config.get(DOMAIN)
    if conf is None:
        return True

    # Initialize hass.data storage for this domain
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("devices", {})

    # Support both single device (dict) and multiple devices (list) configuration
    devices_config = []
    if isinstance(conf, list):
        # Multiple devices configuration
        devices_config = conf
    else:
        # Single device configuration (backward compatibility)
        devices_config = [conf]

    # Set up each device
    for device_conf in devices_config:
        name = device_conf.get("name", DEFAULT_NAME)
        modbus_hub = device_conf.get("modbus_hub")  # name of HA modbus hub to reuse (recommended)
        host = device_conf.get("modbus_host")  # fallback host if no HA modbus hub is used
        port = int(device_conf.get("modbus_port", 502))
        unit = int(device_conf.get("unit", 1))
        poll = int(device_conf.get("poll_interval", 10))
        hvac_map = device_conf.get("hvac_mode_labels", None)

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

        # Create DataUpdateCoordinator for this device
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
        # Use device name + host/port + unit as key to support multiple devices
        device_key = f"{name}_{host or modbus_hub}_{unit}".lower().replace(" ", "_")
        hass.data[DOMAIN]["devices"][device_key] = {
            "hub": hub,
            "coordinator": coordinator,
            "name": name,
            "config": device_conf,
        }

        _LOGGER.info("HA Atrea Recuperation device '%s' initialized from YAML", name)

    # Load platforms using discovery helper (once for all devices)
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

    _LOGGER.info("HA Atrea Recuperation integration initialized with %d device(s)", len(devices_config))
    return True

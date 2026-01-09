"""Config flow for HA Atrea Recuperation integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_MODBUS_HUB,
    CONF_UNIT,
    CONF_POLL_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_UNIT,
    DEFAULT_POLL_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class HaAtreaRecuperationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Atrea Recuperation."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - device name."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data[CONF_NAME] = user_input[CONF_NAME]
            return await self.async_step_connection()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_connection(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle connection type selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            connection_type = user_input.get("connection_type")
            if connection_type == "modbus_hub":
                return await self.async_step_modbus_hub()
            elif connection_type == "direct":
                return await self.async_step_direct_connection()

        # Get available modbus hubs
        available_hubs = await self._get_available_modbus_hubs()
        
        # Build options for selector
        options = []
        if available_hubs:
            options.append(
                selector.SelectOptionDict(value="modbus_hub", label="Use existing Modbus Hub")
            )
        options.append(
            selector.SelectOptionDict(value="direct", label="Direct TCP Connection")
        )

        data_schema = vol.Schema(
            {
                vol.Required("connection_type"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="connection",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "available_hubs": ", ".join(available_hubs) if available_hubs else "None"
            },
        )

    async def async_step_modbus_hub(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle modbus hub selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data[CONF_MODBUS_HUB] = user_input[CONF_MODBUS_HUB]
            return await self.async_step_device_config()

        # Get available modbus hubs
        available_hubs = await self._get_available_modbus_hubs()

        if not available_hubs:
            errors["base"] = "no_modbus_hubs"
            # Redirect to direct connection
            return await self.async_step_direct_connection()

        # Build options for selector
        options = [
            selector.SelectOptionDict(value=hub, label=hub)
            for hub in available_hubs
        ]

        data_schema = vol.Schema(
            {
                vol.Required(CONF_MODBUS_HUB): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="modbus_hub",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_direct_connection(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle direct TCP connection configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data[CONF_HOST] = user_input[CONF_HOST]
            self._data[CONF_PORT] = user_input[CONF_PORT]
            return await self.async_step_device_config()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
                vol.Required(CONF_PORT, default=DEFAULT_PORT): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=65535,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="direct_connection",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_device_config(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device configuration (unit, poll interval)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data[CONF_UNIT] = user_input[CONF_UNIT]
            self._data[CONF_POLL_INTERVAL] = user_input[CONF_POLL_INTERVAL]

            # Check if this device already exists
            await self.async_set_unique_id(self._generate_unique_id(self._data))
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=self._data[CONF_NAME],
                data=self._data,
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_UNIT, default=DEFAULT_UNIT): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=247,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=5,
                        max=300,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="seconds",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="device_config",
            data_schema=data_schema,
            errors=errors,
        )

    async def _get_available_modbus_hubs(self) -> list[str]:
        """Get list of available Modbus hubs.
        
        Note: A modbus hub can be reused with different unit IDs,
        so we return all available hubs from the modbus integration.
        """
        available_hubs = []
        
        # Get modbus hubs from hass.data
        modbus_hubs = self.hass.data.get("modbus", {})
        if isinstance(modbus_hubs, dict):
            all_hub_names = list(modbus_hubs.keys())
        else:
            all_hub_names = []

        return all_hub_names

    def _generate_unique_id(self, data: dict[str, Any]) -> str:
        """Generate a unique ID for this device configuration."""
        # Use modbus_hub + unit or host + port + unit
        if CONF_MODBUS_HUB in data:
            return f"{data[CONF_MODBUS_HUB]}_{data[CONF_UNIT]}"
        else:
            return f"{data[CONF_HOST]}_{data[CONF_PORT]}_{data[CONF_UNIT]}"

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> HaAtreaRecuperationOptionsFlow:
        """Get the options flow for this handler."""
        return HaAtreaRecuperationOptionsFlow(config_entry)


class HaAtreaRecuperationOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for HA Atrea Recuperation."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_POLL_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_POLL_INTERVAL,
                        self.config_entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=5,
                        max=300,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="seconds",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )

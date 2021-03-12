"""Config flow for Vivint integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from aiohttp import ClientResponseError
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from vivintpy.exceptions import VivintSkyApiAuthenticationError, VivintSkyApiError

from .const import DOMAIN  # pylint:disable=unused-import
from .const import (
    CONF_HD_STREAM,
    CONF_RTSP_STREAM,
    DEFAULT_HD_STREAM,
    DEFAULT_RTSP_STREAM,
    RTSP_STREAM_TYPES,
)
from .hub import VivintHub

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Vivint."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            for entry in self._async_current_entries():
                if entry.data[CONF_USERNAME] == user_input[CONF_USERNAME]:
                    return self.async_abort(reason="already_configured")

            hub = VivintHub(self.hass, user_input)
            try:
                await hub.login()
            except VivintSkyApiAuthenticationError:
                errors["base"] = "invalid_auth"
            except (VivintSkyApiError, ClientResponseError):
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    """Handle Vivint options."""

    def __init__(self, config_entry):
        """Initialize Vivint options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Manage Vivint options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_HD_STREAM,
                        default=self.config_entry.options.get(
                            CONF_HD_STREAM, DEFAULT_HD_STREAM
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_RTSP_STREAM,
                        default=self.config_entry.options.get(
                            CONF_RTSP_STREAM, DEFAULT_RTSP_STREAM
                        ),
                    ): vol.In(RTSP_STREAM_TYPES),
                }
            ),
        )

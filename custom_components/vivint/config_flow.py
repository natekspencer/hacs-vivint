"""Config flow for Vivint integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from aiohttp import ClientResponseError
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from pyvivint.vivint import Vivint

from .const import (
    CONF_HD_STREAM,
    CONF_RTSP_STREAM,
    DEFAULT_HD_STREAM,
    DEFAULT_RTSP_STREAM,
    DOMAIN,
    RTSP_STREAM_TYPES,
)

_LOGGER = logging.getLogger(__name__)


class VivintFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Vivint config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return VivintOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}

        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            try:
                _LOGGER.debug("Attempting to login to Vivint API.")
                api = Vivint(user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
                await api.connect()
                _LOGGER.debug("Successfully logged in.")
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )
            except ClientResponseError:
                errors["base"] = "cannot_connect"
                _LOGGER.debug(
                    "Unable to login to Vivint API, please check credentials."
                )
            except Exception:
                errors["base"] = "unknown"
                _LOGGER.debug("Unable to login to Vivint API, please try again later.")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
            ),
            errors=errors,
        )


class VivintOptionsFlowHandler(config_entries.OptionsFlow):
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

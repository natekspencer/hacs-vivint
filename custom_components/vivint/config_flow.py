"""Config flow for Vivint integration."""
import voluptuous as vol
from aiohttp import ClientResponseError
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from pyvivint.vivint import Vivint

from .const import _LOGGER, VIVINT_DOMAIN


class VivintFlowHandler(config_entries.ConfigFlow, domain=VIVINT_DOMAIN):
    """Handle a Vivint config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

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

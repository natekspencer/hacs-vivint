"""Config flow for Vivint integration."""
import logging
from typing import Any, Dict, Optional

from aiohttp import ClientResponseError
from aiohttp.client_exceptions import ClientConnectorError
from vivintpy.exceptions import (
    VivintSkyApiAuthenticationError,
    VivintSkyApiError,
    VivintSkyApiMfaRequiredError,
)
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback

from .const import (
    CONF_HD_STREAM,
    CONF_MFA,
    CONF_RTSP_STREAM,
    CONF_RTSP_URL_LOGGING,
    DEFAULT_HD_STREAM,
    DEFAULT_RTSP_STREAM,
    DEFAULT_RTSP_URL_LOGGING,
    RTSP_STREAM_TYPES,
)
from .const import DOMAIN  # pylint:disable=unused-import
from .hub import VivintHub

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
)

STEP_MFA_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MFA): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Vivint."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        self._hub: VivintHub = None

    async def async_create_entry(self):
        """Create the config entry."""
        existing_entry = await self.async_set_unique_id(DOMAIN)

        config_data = {
            CONF_USERNAME: self._hub._data[CONF_USERNAME],
            CONF_PASSWORD: self._hub._data[CONF_PASSWORD],
        }

        if existing_entry:
            self.hass.config_entries.async_update_entry(
                existing_entry, data=config_data
            )
            await self.hass.config_entries.async_reload(existing_entry.entry_id)
            return self.async_abort(reason="reauth_successful")

        await self._hub.disconnect()
        return super().async_create_entry(
            title=config_data[CONF_USERNAME], data=config_data
        )

    async def async_vivint_login(self, step_id, user_input, schema):
        errors = {}

        self._hub = VivintHub(self.hass, user_input)
        try:
            await self._hub.login(load_devices=True)
        except VivintSkyApiMfaRequiredError:
            return await self.async_step_mfa()
        except VivintSkyApiAuthenticationError:
            errors["base"] = "invalid_auth"
        except (VivintSkyApiError, ClientResponseError, ClientConnectorError):
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        if not errors:
            return await self.async_create_entry()

        return self.async_show_form(step_id=step_id, data_schema=schema, errors=errors)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            for entry in self._async_current_entries():
                if entry.data[CONF_USERNAME] == user_input[CONF_USERNAME]:
                    return self.async_abort(reason="already_configured")

            return await self.async_vivint_login(
                step_id="user", user_input=user_input, schema=STEP_USER_DATA_SCHEMA
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_mfa(self, user_input=None):
        """Handle a multi-factor authentication (MFA) flow."""
        if user_input is None:
            return self.async_show_form(step_id="mfa", data_schema=STEP_MFA_DATA_SCHEMA)

        try:
            await self._hub.verify_mfa(user_input[CONF_MFA])
        except Exception as ex:
            _LOGGER.error(ex)
            return self.async_show_form(
                step_id="mfa",
                data_schema=STEP_MFA_DATA_SCHEMA,
                errors={"base": "unknown"},
            )

        return await self.async_create_entry()

    async def async_step_reauth(self, user_input=None):
        """Perform reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Dialog that informs the user that reauth is required."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm", data_schema=STEP_USER_DATA_SCHEMA
            )

        return await self.async_vivint_login(
            step_id="reauth_confirm",
            user_input=user_input,
            schema=STEP_USER_DATA_SCHEMA,
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
                    vol.Optional(
                        CONF_RTSP_URL_LOGGING,
                        default=self.config_entry.options.get(
                            CONF_RTSP_URL_LOGGING, DEFAULT_RTSP_URL_LOGGING
                        ),
                    ): bool,
                }
            ),
        )

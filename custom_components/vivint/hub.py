"""A wrapper 'hub' for the Vivint API and base entity for common attributes."""
from datetime import timedelta
import logging
import os
from typing import Any, Callable, Dict, Optional, Tuple

import aiohttp
from aiohttp import ClientResponseError
from aiohttp.client import ClientSession
from aiohttp.client_exceptions import ClientConnectorError
from vivintpy.account import Account
from vivintpy.devices import VivintDevice
from vivintpy.devices.alarm_panel import AlarmPanel
from vivintpy.entity import UPDATE
from vivintpy.exceptions import (
    VivintSkyApiAuthenticationError,
    VivintSkyApiError,
    VivintSkyApiMfaRequiredError,
)

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DEFAULT_CACHEDB, DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = 300


@callback
def get_device_id(device: VivintDevice) -> Tuple[str, str]:
    """Get device registry identifier for device."""
    return (DOMAIN, f"{device.panel_id}-{device.id}")


class VivintHub:
    """A Vivint hub wrapper class."""

    def __init__(
        self, hass: HomeAssistant, data: dict, undo_listener: Optional[Callable] = None
    ):
        """Initialize the Vivint hub."""
        self._data = data
        self.undo_listener = undo_listener
        self.account: Account = None
        self.logged_in = False

        async def _async_update_data():
            """Update all device states from the Vivint API."""
            return await self.account.refresh()

        self.coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=_async_update_data,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def login(
        self, load_devices: bool = False, subscribe_for_realtime_updates: bool = False
    ):
        """Login to Vivint."""
        self.logged_in = False

        # Get previous session if available
        abs_cookie_jar = aiohttp.CookieJar()
        try:
            abs_cookie_jar.load(self.cache_file())
        except:
            _LOGGER.debug("No previous session found")

        self.account = Account(
            username=self._data[CONF_USERNAME],
            password=self._data[CONF_PASSWORD],
            persist_session=True,
            client_session=ClientSession(cookie_jar=abs_cookie_jar),
        )
        try:
            await self.account.connect(
                load_devices=load_devices,
                subscribe_for_realtime_updates=subscribe_for_realtime_updates,
            )
            return self.save_session()
        except VivintSkyApiMfaRequiredError as ex:
            raise ex
        except VivintSkyApiAuthenticationError as ex:
            _LOGGER.error("Invalid credentials")
            raise ex
        except (VivintSkyApiError, ClientResponseError, ClientConnectorError) as ex:
            _LOGGER.error("Unable to connect to the Vivint API")
            raise ex

    async def verify_mfa(self, code: str):
        try:
            await self.account.verify_mfa(code)
            return self.save_session()
        except Exception as ex:
            raise ex

    def cache_file(self):
        return self.coordinator.hass.config.path(DEFAULT_CACHEDB)

    def remove_cache_file(self):
        """Remove the cached session file."""
        os.remove(self.cache_file())

    def save_session(self):
        """Save session for reuse."""
        self.account.vivintskyapi._VivintSkyApi__client_session.cookie_jar.save(
            self.cache_file()
        )
        self.logged_in = True
        return self.logged_in


class VivintEntity(CoordinatorEntity):
    """Generic Vivint entity representing common data and methods."""

    def __init__(self, device: VivintDevice, hub: VivintHub):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(hub.coordinator)
        self.device = device
        self.hub = hub

    @callback
    def _update_callback(self, _) -> None:
        """Call from dispatcher when state changes."""
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Set up a listener for the entity."""
        await super().async_added_to_hass()
        self.device.on(UPDATE, self._update_callback)

    @property
    def name(self):
        """Return the name of this entity."""
        return self.device.name

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return the device information for a Vivint device."""
        return {
            "identifiers": {get_device_id(self.device)},
            "name": self.device.name,
            "manufacturer": self.device.manufacturer,
            "model": self.device.model,
            "sw_version": self.device.software_version,
            "via_device": None
            if type(self.device) is AlarmPanel
            else (DOMAIN, self.device.alarm_panel.id),
        }

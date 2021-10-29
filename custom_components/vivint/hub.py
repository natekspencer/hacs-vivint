"""A wrapper 'hub' for the Vivint API and base entity for common attributes."""
from __future__ import annotations

from datetime import timedelta
import logging
import os
from typing import Any, Callable, Optional, Tuple

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
    return (
        DOMAIN,
        f"{device.panel_id}-{device.parent.id if device.is_subdevice else device.id}",
    )


class VivintHub:
    """A Vivint hub wrapper class."""

    def __init__(
        self, hass: HomeAssistant, data: dict, undo_listener: Optional[Callable] = None
    ) -> None:
        """Initialize the Vivint hub."""
        self._data = data
        self.__undo_listener = undo_listener
        self.account: Account = None
        self.logged_in = False
        self.session: ClientSession = None

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

        self.session = ClientSession(cookie_jar=abs_cookie_jar)

        self.account = Account(
            username=self._data[CONF_USERNAME],
            password=self._data[CONF_PASSWORD],
            persist_session=True,
            client_session=self.session,
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

    async def disconnect(self, remove_cache: bool = False) -> None:
        """Disconnect from Vivint, close the session and optionally remove cache."""
        if self.account.connected:
            await self.account.disconnect()
        if not self.session.closed:
            await self.session.close()
        if remove_cache:
            self.remove_cache_file()
        if self.__undo_listener:
            self.__undo_listener()
            self.__undo_listener = None

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

    def __init__(self, device: VivintDevice, hub: VivintHub) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(hub.coordinator)
        self.device = device
        self.hub = hub

    async def async_added_to_hass(self) -> None:
        """Set up a listener for the entity."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.device.on(UPDATE, lambda _: self.async_write_ha_state())
        )

    @property
    def name(self):
        """Return the name of this entity."""
        return self.device.name

    @property
    def device_info(self) -> dict[str, Any]:
        """Return the device information for a Vivint device."""
        device = self.device.parent if self.device.is_subdevice else self.device
        return {
            "identifiers": {get_device_id(device)},
            "name": device.name if device.name else type(device).__name__,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "sw_version": device.software_version,
            "via_device": None
            if isinstance(device, AlarmPanel)
            else (DOMAIN, device.alarm_panel.id),
        }

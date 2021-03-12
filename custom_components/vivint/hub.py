"""A wrapper 'hub' for the Vivint API and base entity for common attributes."""
import logging
from datetime import timedelta
from typing import Any, Callable, Dict, Optional

import vivintpy.account
from aiohttp import ClientResponseError
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from vivintpy.devices.alarm_panel import AlarmPanel
from vivintpy.exceptions import VivintSkyApiAuthenticationError, VivintSkyApiError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = 300


class VivintHub:
    """A Vivint hub wrapper class."""

    def __init__(
        self, hass: HomeAssistant, data: dict, undo_listener: Optional[Callable] = None
    ):
        """Initialize the Vivint hub."""
        self._data = data
        self.undo_listener = undo_listener
        self.account: vivintpy.account.Account = None
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
        self.account = vivintpy.account.Account(
            username=self._data[CONF_USERNAME], password=self._data[CONF_PASSWORD]
        )
        try:
            await self.account.connect(
                load_devices=load_devices,
                subscribe_for_realtime_updates=subscribe_for_realtime_updates,
            )
            self.logged_in = True
            return self.logged_in
        except VivintSkyApiAuthenticationError as ex:
            _LOGGER.error("Invalid credentials")
            raise ex
        except (VivintSkyApiError, ClientResponseError) as ex:
            _LOGGER.error("Unable to connect to the Vivint API")
            raise ex


class VivintEntity(CoordinatorEntity):
    """Generic Vivint entity representing common data and methods."""

    def __init__(self, device: vivintpy.devices.VivintDevice, hub: VivintHub):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(hub.coordinator)
        self.device = device
        self.hub = hub

    @callback
    def _update_callback(self) -> None:
        """Call from dispatcher when state changes."""
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Set up a listener for the entity."""
        await super().async_added_to_hass()
        self.device.add_update_callback(self._update_callback)

    @property
    def name(self):
        """Return the name of this entity."""
        return self.device.name

    # @property
    # def unique_id(self):
    #     """Return a unique ID."""
    #     return f"{self.robot.serial}-{self.entity_type}"

    # @property
    # def available(self):
    #     """Return availability."""
    #     return self.hub.logged_in

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return the device information for a Vivint device."""
        return {
            "identifiers": {(DOMAIN, self.device.serial_number or self.unique_id)},
            "name": self.device.name,
            "manufacturer": self.device.manufacturer,
            "model": self.device.model,
            "sw_version": self.device.software_version,
            "via_device": None
            if type(self.device) is AlarmPanel
            else (DOMAIN, self.device.alarm_panel.id),
        }

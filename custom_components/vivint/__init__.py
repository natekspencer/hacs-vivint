"""The Vivint integration."""
import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from aiohttp import ClientResponseError
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from pyvivint.devices import VivintDevice
from pyvivint.devices.alarm_panel import AlarmPanel
from pyvivint.vivint import Vivint

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    "alarm_control_panel",
    "binary_sensor",
    "camera",
    "cover",
    "light",
    "lock",
    "sensor",
    "switch",
]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Vivint component."""
    hass.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Vivint from a config entry."""
    undo_listener = entry.add_update_listener(update_listener)

    hub = VivintHub(hass, entry.data, undo_listener)

    await hub.login()
    if not hub.logged_in:
        _LOGGER.debug("Failed to login to Vivint API")
        return False

    hass.data[DOMAIN][entry.entry_id] = hub

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    hub = hass.data[DOMAIN][entry.entry_id]
    await hub.api.disconnect()
    hub.undo_listener()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


class VivintHub:
    """A Vivint hub wrapper class."""

    def __init__(self, hass, domain_config, undo_listener):
        """Initialize the Vivint hub."""
        self.config = domain_config
        self.undo_listener = undo_listener
        self.api = None
        self.logged_in = False

        async def async_update_data():
            """Update all device states from the Vivint API."""
            return await self.api.refresh()

        self.coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=async_update_data,
            update_interval=timedelta(minutes=5),
        )

    async def login(self):
        """Login to Vivint."""
        _LOGGER.debug("Trying to connect to Vivint API")
        try:
            self.api = Vivint(self.config[CONF_USERNAME], self.config[CONF_PASSWORD])
            await self.api.connect(
                load_devices=True, subscribe_for_realtime_updates=True
            )
        except ClientResponseError as ex:
            _LOGGER.error("Unable to connect to Vivint API")
            raise ConfigEntryNotReady from ex
        except Exception as ex:
            _LOGGER.error(f"Unknown error: {ex}")
            raise ConfigEntryNotReady from ex

        self.logged_in = True
        _LOGGER.debug("Successfully connected to Vivint API")


class VivintEntity(CoordinatorEntity):
    """Generic Vivint entity representing common data and methods."""

    def __init__(self, hub: VivintHub, device: VivintDevice):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(hub.coordinator)
        self.hub = hub
        self.device = device

    async def async_added_to_hass(self) -> None:
        """Set up a listener for the entity."""
        await super().async_added_to_hass()
        self.device.add_update_callback(self._update_callback)

    @callback
    def _update_callback(self) -> None:
        """Call from dispatcher when state changes."""
        self.async_write_ha_state()

    @property
    def name(self):
        """Return the name of this entity."""
        return self.device.name

    @property
    def available(self):
        """Return availability."""
        return self.hub.logged_in

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

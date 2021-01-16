"""The Vivint integration."""
import asyncio
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from aiohttp import ClientResponseError
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from pyvivintsky import VivintSky

from .const import _LOGGER, VIVINT_DOMAIN, VIVINT_PLATFORMS

CONFIG_SCHEMA = vol.Schema(
    {
        VIVINT_DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict):
    """Setup the Vivint component."""
    hass.data[VIVINT_DOMAIN] = {}

    if VIVINT_DOMAIN not in config:
        return True

    for entry in config[VIVINT_DOMAIN]:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                VIVINT_DOMAIN, context={"source": SOURCE_IMPORT}, data=entry
            )
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up config entry."""
    hub = VivintHub(hass, entry.data)

    await hub.login()
    if not hub.logged_in:
        _LOGGER.debug("Failed to login to Vivint API")
        return False

    hass.data[VIVINT_DOMAIN][entry.entry_id] = hub

    for component in VIVINT_PLATFORMS:
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
                for component in VIVINT_PLATFORMS
            ]
        )
    )

    hass.data[VIVINT_DOMAIN][entry.entry_id].api.disconnect()

    if unload_ok:
        hass.data[VIVINT_DOMAIN].pop(entry.entry_id)

    return unload_ok


class VivintHub:
    """A Vivint hub wrapper class."""

    def __init__(self, hass, domain_config):
        """Initialize the Vivint hub."""
        self.config = domain_config
        self._hass = hass
        self.api = None
        self.logged_in = False

        # async def async_update_data():
        #     """Update all device states from the Vivint API."""
        #     for panel_id in self.api.get_panels():
        #         panel = self.api.get_panel(panel_id)
        #         await panel.poll_devices()
        #     return True

        self.coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=VIVINT_DOMAIN,
            # update_method=async_update_data,
            update_interval=timedelta(days=1),
        )

    async def login(self):
        """Login to Vivint."""
        _LOGGER.debug("Trying to connect to Vivint API")
        try:
            self.api = VivintSky(self.config[CONF_USERNAME], self.config[CONF_PASSWORD])
            await self.api.connect()
        except ClientResponseError as ex:
            _LOGGER.error("Unable to connect to Vivint API")
            raise ConfigEntryNotReady from ex
        except Exception as ex:
            _LOGGER.error(f"Unknown error: {ex}")
            raise ConfigEntryNotReady from ex

        self.logged_in = True
        _LOGGER.debug("Successfully connected to Vivint API")


# class VivintEntity(CoordinatorEntity):
#     """Generic Vivint entity representing common data and methods."""

#     def __init__(self, type, hub: VivintHub):
#         """Pass coordinator to CoordinatorEntity."""
#         super().__init__(hub.coordinator)
#         self.type = type if type else ""
#         self.hub = hub

#     @property
#     def available(self):
#         """Return availability."""
#         return self.hub.logged_in

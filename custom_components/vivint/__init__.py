"""The Vivint integration."""
import asyncio
import logging

from aiohttp import ClientResponseError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from vivintpy.exceptions import VivintSkyApiAuthenticationError, VivintSkyApiError

from .const import DOMAIN
from .hub import VivintHub

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    "alarm_control_panel",
    "binary_sensor",
    "camera",
    "climate",
    "cover",
    "light",
    "lock",
    "sensor",
    "switch",
]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Vivint domain."""
    hass.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Vivint from a config entry."""
    undo_listener = entry.add_update_listener(update_listener)

    hub = hass.data[DOMAIN][entry.entry_id] = VivintHub(hass, entry.data, undo_listener)

    try:
        await hub.login(load_devices=True, subscribe_for_realtime_updates=True)
    except VivintSkyApiAuthenticationError:
        return False
    except (VivintSkyApiError, ClientResponseError) as ex:
        raise ConfigEntryNotReady from ex

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    hub = hass.data[DOMAIN][entry.entry_id]
    await hub.account.disconnect()
    hub.undo_listener()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

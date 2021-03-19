"""The Vivint integration."""
import asyncio

from aiohttp import ClientResponseError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_DEVICE_ID, ATTR_DOMAIN
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry
from vivintpy.devices import VivintDevice
from vivintpy.devices.camera import DOORBELL_DING, MOTION_DETECTED, Camera
from vivintpy.enums import CapabilityCategoryType
from vivintpy.exceptions import VivintSkyApiAuthenticationError, VivintSkyApiError

from .const import DOMAIN, EVENT_TYPE
from .hub import VivintHub, get_device_id

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

ATTR_TYPE = "type"


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

    dev_reg = await device_registry.async_get_registry(hass)

    @callback
    def async_on_device_event(event_type: str, viv_device: VivintDevice) -> None:
        """Relay Vivint device event to hass."""
        device = dev_reg.async_get_device({get_device_id(viv_device)})
        hass.bus.async_fire(
            EVENT_TYPE,
            {
                ATTR_TYPE: event_type,
                ATTR_DOMAIN: DOMAIN,
                ATTR_DEVICE_ID: device.id,
            },
        )

    for system in hub.account.systems:
        for alarm_panel in system.alarm_panels:
            for device in alarm_panel.get_devices([Camera]):
                device.on(
                    MOTION_DETECTED,
                    lambda event: async_on_device_event(
                        MOTION_DETECTED, event["device"]
                    ),
                )
                if CapabilityCategoryType.DOORBELL in device.capabilities.keys():
                    device.on(
                        DOORBELL_DING,
                        lambda event: async_on_device_event(
                            DOORBELL_DING, event["device"]
                        ),
                    )

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

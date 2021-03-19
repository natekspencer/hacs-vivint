"""Provides device triggers for Vivint."""
from typing import List, Optional

import voluptuous as vol
from homeassistant.components.automation import AutomationActionType
from homeassistant.components.device_automation import TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.typing import ConfigType
from vivintpy.devices import VivintDevice
from vivintpy.devices.camera import DOORBELL_DING, MOTION_DETECTED, Camera
from vivintpy.enums import CapabilityCategoryType

from .const import DOMAIN, EVENT_TYPE
from .hub import VivintHub

TRIGGER_TYPES = {MOTION_DETECTED, DOORBELL_DING}

TRIGGER_SCHEMA = TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
    }
)


async def async_get_vivint_device(
    hass: HomeAssistant, device_id: str
) -> Optional[VivintDevice]:
    """Get a Vivint device for the given device registry id."""
    device_registry: DeviceRegistry = (
        await hass.helpers.device_registry.async_get_registry()
    )
    registry_device = device_registry.async_get(device_id)
    identifier = list(list(registry_device.identifiers)[0])[1]
    [panel_id, vivint_device_id] = [int(item) for item in identifier.split("-")]
    for config_entry_id in registry_device.config_entries:
        hub: VivintHub = hass.data[DOMAIN].get(config_entry_id)
        for system in hub.account.systems:
            if system.id != panel_id:
                continue
            for alarm_panel in system.alarm_panels:
                for device in alarm_panel.devices:
                    if device.id == vivint_device_id:
                        return device
    return None


async def async_get_triggers(hass: HomeAssistant, device_id: str) -> List[dict]:
    """Return a list of triggers."""
    device = await async_get_vivint_device(hass, device_id)

    triggers = []

    if device and isinstance(device, Camera):
        triggers.append(
            {
                CONF_PLATFORM: "device",
                CONF_DOMAIN: DOMAIN,
                CONF_DEVICE_ID: device_id,
                CONF_TYPE: MOTION_DETECTED,
            }
        )
        if CapabilityCategoryType.DOORBELL in device.capabilities.keys():
            triggers.append(
                {
                    CONF_PLATFORM: "device",
                    CONF_DOMAIN: DOMAIN,
                    CONF_DEVICE_ID: device_id,
                    CONF_TYPE: DOORBELL_DING,
                }
            )

    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: AutomationActionType,
    automation_info: dict,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    config = TRIGGER_SCHEMA(config)
    event_config = event_trigger.TRIGGER_SCHEMA(
        {
            event_trigger.CONF_PLATFORM: "event",
            event_trigger.CONF_EVENT_TYPE: EVENT_TYPE,
            event_trigger.CONF_EVENT_DATA: {
                CONF_DEVICE_ID: config[CONF_DEVICE_ID],
                CONF_TYPE: config[CONF_TYPE],
            },
        }
    )
    return await event_trigger.async_attach_trigger(
        hass, event_config, action, automation_info, platform_type="device"
    )

"""Support for Vivint switches."""
from homeassistant.components.switch import SwitchEntity
from vivintpy.devices.switch import BinarySwitch

from .const import DOMAIN
from .hub import VivintEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint switches using config entry."""
    entities = []
    hub = hass.data[DOMAIN][config_entry.entry_id]

    for system in hub.account.systems:
        for alarm_panel in system.alarm_panels:
            for device in alarm_panel.devices:
                if type(device) is BinarySwitch:
                    entities.append(VivintSwitchEntity(device=device, hub=hub))

    if not entities:
        return

    async_add_entities(entities, True)


class VivintSwitchEntity(VivintEntity, SwitchEntity):
    """Vivint Switch."""

    @property
    def is_on(self):
        """Return True if the switch is on."""
        return self.device.is_on

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.device.alarm_panel.id}-{self.device.id}"

    async def async_turn_on(self, **kwargs):
        """Turn on the switch."""
        await self.device.turn_on()

    async def async_turn_off(self, **kwargs):
        """Turn off the switch."""
        await self.device.turn_off()

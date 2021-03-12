"""Support for Vivint lights."""
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    SUPPORT_BRIGHTNESS,
    LightEntity,
)
from vivintpy.devices.switch import MultilevelSwitch

from .const import DOMAIN
from .hub import VivintEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint lights using config entry."""
    entities = []
    hub = hass.data[DOMAIN][config_entry.entry_id]

    for system in hub.account.systems:
        for alarm_panel in system.alarm_panels:
            for device in alarm_panel.devices:
                if type(device) is MultilevelSwitch:
                    entities.append(VivintLightEntity(device=device, hub=hub))

    if not entities:
        return

    async_add_entities(entities, True)


class VivintLightEntity(VivintEntity, LightEntity):
    """Vivint Light."""

    @property
    def is_on(self):
        """Return True if the light is on."""
        return self.device.is_on

    @property
    def brightness(self):
        """Return the brightness of the light between 0..255.

        Vivint multilevel switches use a range of 0..100 to control brightness.
        """
        if self.device.level is not None:
            return round((self.device.level / 100) * 255)
        return 0

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.device.alarm_panel.id}-{self.device.id}"

    async def async_turn_on(self, **kwargs):
        """Turn on the light."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)

        if brightness is None:
            # Just turn on the light, which will restore previous brightness.
            await self.device.turn_on()
        else:
            # Vivint multilevel switches use a range of 0..100 to control brightness.
            level = byte_to_vivint_level(brightness)
            await self.device.set_level(level)

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        await self.device.turn_off()


def byte_to_vivint_level(value: int) -> int:
    """Convert brightness from 0..255 scale to 0..100 scale.

    `value` -- (int) Brightness byte value from 0-255.
    """
    if value > 0:
        return max(1, round((value / 255) * 100))
    return 0

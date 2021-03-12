"""Support for Vivint garage doors."""
from homeassistant.components.cover import (
    DEVICE_CLASS_GARAGE,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    CoverEntity,
)
from vivintpy.devices.garage_door import GarageDoor

from .const import DOMAIN
from .hub import VivintEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint garage doors using config entry."""
    entities = []
    hub = hass.data[DOMAIN][config_entry.entry_id]

    for system in hub.account.systems:
        for alarm_panel in system.alarm_panels:
            for device in alarm_panel.devices:
                if type(device) is GarageDoor:
                    entities.append(VivintGarageDoorEntity(device=device, hub=hub))

    if not entities:
        return

    async_add_entities(entities, True)


class VivintGarageDoorEntity(VivintEntity, CoverEntity):
    """Vivint Garage Door."""

    @property
    def is_opening(self) -> bool:
        """Return whether this device is opening."""
        return self.device.is_opening

    @property
    def is_closing(self) -> bool:
        """Return whether this device is closing."""
        return self.device.is_closing

    @property
    def is_closed(self) -> bool:
        """Return whether this device is closed."""
        return self.device.is_closed

    @property
    def device_class(self):
        """Return the list of supported features."""
        return DEVICE_CLASS_GARAGE

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return SUPPORT_CLOSE | SUPPORT_OPEN

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.device.alarm_panel.id}-{self.device.id}"

    async def async_close_cover(self, **kwargs):
        """Close cover."""
        await self.device.close()

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        await self.device.open()

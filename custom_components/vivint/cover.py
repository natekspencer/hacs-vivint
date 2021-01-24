"""Support for Vivint garage doors."""
from homeassistant.components.cover import (
    DEVICE_CLASS_GARAGE,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    CoverEntity,
)
from pyvivint.devices.garage_door import GarageDoor

from . import VivintEntity
from .const import _LOGGER, VIVINT_DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint garage doors using config entry."""
    entities = []
    hub = hass.data[VIVINT_DOMAIN][config_entry.entry_id]

    for system in hub.api.systems:
        for alarm_panel in system.alarm_panels:
            for device in alarm_panel.devices:
                if type(device) is GarageDoor:
                    entities.append(VivintGarageDoorEntity(hub, device))

    if not entities:
        return

    _LOGGER.debug(f"Adding Vivint garage doors: {entities}")
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

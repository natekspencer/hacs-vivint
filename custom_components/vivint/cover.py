"""Support for Vivint garage doors."""
from typing import Any, Dict

from homeassistant.components.cover import (
    DEVICE_CLASS_GARAGE,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    CoverEntity,
)
from homeassistant.core import callback
from pyvivintsky import VivintGarageDoor

from . import VivintHub
from .const import _LOGGER, VIVINT_DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint garage doors using config entry."""
    entities = []
    hub = hass.data[VIVINT_DOMAIN][config_entry.entry_id]

    for panel_id in hub.api.get_panels():
        panel = hub.api.get_panel(panel_id)
        for device_id in panel.get_devices():
            device = panel.get_device(device_id)
            if type(device) is VivintGarageDoor:
                entities.append(VivintGarageDoorEntity(hub, device))

    if not entities:
        return

    _LOGGER.debug(f"Adding Vivint garage doors: {entities}")
    async_add_entities(entities, True)


class VivintGarageDoorEntity(CoverEntity):
    """Vivint Garage Door."""

    def __init__(self, hub: VivintHub, device):
        self.hub = hub
        self.device = device

    async def async_added_to_hass(self) -> None:
        """Set up a listener for the entity."""
        self.device._callback = self._update_callback

    @callback
    def _update_callback(self) -> None:
        """Call from dispatcher when state changes."""
        self.async_write_ha_state()

    @property
    def is_opening(self) -> bool:
        """Return whether this device is opening."""
        return self.device.state == VivintGarageDoor.GarageDoorState.Opening

    @property
    def is_closing(self) -> bool:
        """Return whether this device is closing."""
        return self.device.state == VivintGarageDoor.GarageDoorState.Closing

    @property
    def is_closed(self) -> bool:
        """Return whether this device is closed."""
        return (
            None
            if self.device.state == VivintGarageDoor.GarageDoorState.Unknown
            else self.device.state == VivintGarageDoor.GarageDoorState.Closed
        )

    @property
    def device_class(self):
        """Return the list of supported features."""
        return DEVICE_CLASS_GARAGE

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return SUPPORT_CLOSE | SUPPORT_OPEN

    @property
    def name(self):
        """Return the name of this entity."""
        return self.device.name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.device.get_root().id}-{self.device.id}"

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return the device information for a Vivint garage door."""
        return {
            "identifiers": {(VIVINT_DOMAIN, self.device.serial_number)},
            "name": self.device.name,
            "manufacturer": self.device.manufacturer,
            "model": self.device.model,
            "sw_version": self.device.software_version,
            "via_device": (VIVINT_DOMAIN, self.device.get_root().id),
        }

    async def async_close_cover(self, **kwargs):
        """Close cover."""
        await self.device.close_garage_door()

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        await self.device.open_garage_door()

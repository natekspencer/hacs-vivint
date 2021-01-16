"""Support for Vivint door locks."""
from typing import Any, Dict

from homeassistant.components.lock import LockEntity
from homeassistant.core import callback
from pyvivintsky import VivintDoorLock

from . import VivintHub
from .const import _LOGGER, VIVINT_DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint door locks using config entry."""
    entities = []
    hub = hass.data[VIVINT_DOMAIN][config_entry.entry_id]

    for panel_id in hub.api.get_panels():
        panel = hub.api.get_panel(panel_id)
        for device_id in panel.get_devices():
            device = panel.get_device(device_id)
            if type(device) is VivintDoorLock:
                entities.append(VivintLockEntity(hub, device))

    if not entities:
        return

    _LOGGER.debug(f"Adding Vivint door locks: {entities}")
    async_add_entities(entities, True)


class VivintLockEntity(LockEntity):
    """Vivint Lock."""

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
    def is_locked(self):
        """Return true if the lock is locked."""
        return self.device.state == "Locked"

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

    async def async_lock(self, **kwargs):
        """Lock the lock."""
        await self.device.lock()

    async def async_unlock(self, **kwargs):
        """Unlock the lock."""
        await self.device.unlock()

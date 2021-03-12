"""Support for Vivint door locks."""
from homeassistant.components.lock import LockEntity
from vivintpy.devices.door_lock import DoorLock

from .const import DOMAIN
from .hub import VivintEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint door locks using config entry."""
    entities = []
    hub = hass.data[DOMAIN][config_entry.entry_id]

    for system in hub.account.systems:
        for alarm_panel in system.alarm_panels:
            for device in alarm_panel.devices:
                if type(device) is DoorLock:
                    entities.append(VivintLockEntity(device=device, hub=hub))

    if not entities:
        return

    async_add_entities(entities, True)


class VivintLockEntity(VivintEntity, LockEntity):
    """Vivint Lock."""

    @property
    def is_locked(self):
        """Return true if the lock is locked."""
        return self.device.is_locked

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.device.alarm_panel.id}-{self.device.id}"

    async def async_lock(self, **kwargs):
        """Lock the lock."""
        await self.device.lock()

    async def async_unlock(self, **kwargs):
        """Unlock the lock."""
        await self.device.unlock()

"""Support for Vivint sensors."""
from typing import Any, Dict

from homeassistant.const import DEVICE_CLASS_BATTERY, PERCENTAGE
from homeassistant.helpers.entity import Entity
from pyvivint.devices import UnknownDevice
from pyvivint.devices.camera import Camera
from pyvivint.devices.garage_door import GarageDoor

from . import VivintEntity
from .const import _LOGGER, VIVINT_DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint sensors using config entry."""
    entities = []
    hub = hass.data[VIVINT_DOMAIN][config_entry.entry_id]

    for system in hub.api.systems:
        for alarm_panel in system.alarm_panels:
            for device in alarm_panel.devices:
                if (
                    type(device) not in [UnknownDevice, Camera, GarageDoor]
                    and device.battery_level is not None
                ):
                    entities.append(VivintSensorEntity(hub, device))

    if not entities:
        return

    _LOGGER.debug(f"Adding Vivint sensors: {entities}")
    async_add_entities(entities, True)


class VivintSensorEntity(VivintEntity, Entity):
    """Vivint Sensor."""

    @property
    def name(self):
        """Return the name of this entity."""
        return f"{self.device.name} Battery Level"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.device.alarm_panel.id}-{self.device.id}"

    @property
    def state(self):
        """Return the state."""
        return self.device.battery_level

    @property
    def unit_of_measurement(self):
        """Return unit of measurement."""
        return PERCENTAGE

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_BATTERY

"""Support for Vivint sensors."""
from typing import Any, Dict

from homeassistant.const import DEVICE_CLASS_BATTERY, PERCENTAGE
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity
from pyvivintsky import VivintUnknownDevice

from . import VivintHub
from .const import _LOGGER, VIVINT_DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint sensors using config entry."""
    entities = []
    hub = hass.data[VIVINT_DOMAIN][config_entry.entry_id]

    for panel_id in hub.api.get_panels():
        panel = hub.api.get_panel(panel_id)
        for device_id in panel.get_devices():
            device = panel.get_device(device_id)
            if (
                type(device) is not VivintUnknownDevice
                and device.battery_level is not None
            ):
                entities.append(VivintSensorEntity(hub, device))

    if not entities:
        return

    _LOGGER.debug(f"Adding Vivint sensors: {entities}")
    async_add_entities(entities, True)


class VivintSensorEntity(Entity):
    """Vivint Sensor."""

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
    def name(self):
        """Return the name of this entity."""
        return f"{self.device.name} Battery Level"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.device.get_root().id}-{self.device.id}"

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

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return the device information for a Vivint sensor."""
        return {
            "identifiers": {(VIVINT_DOMAIN, self.device.serial_number)},
            "name": self.device.name,
            "manufacturer": self.device.manufacturer,
            "model": self.device.model,
            "sw_version": self.device.software_version,
            "via_device": (VIVINT_DOMAIN, self.device.get_root().id),
        }

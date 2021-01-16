"""Support for Vivint binary sensors."""
from typing import Any, Dict

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_COLD,
    DEVICE_CLASS_DOOR,
    DEVICE_CLASS_GAS,
    DEVICE_CLASS_HEAT,
    DEVICE_CLASS_MOISTURE,
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_SAFETY,
    DEVICE_CLASS_SMOKE,
    DEVICE_CLASS_WINDOW,
    BinarySensorEntity,
)
from homeassistant.core import callback
from pyvivintsky import VivintWirelessSensor

from . import VivintHub
from .const import _LOGGER, VIVINT_DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint binary sensors using config entry."""
    entities = []
    hub = hass.data[VIVINT_DOMAIN][config_entry.entry_id]

    for panel_id in hub.api.get_panels():
        panel = hub.api.get_panel(panel_id)
        for device_id in panel.get_devices():
            device = panel.get_device(device_id)
            if type(device) is VivintWirelessSensor:
                entities.append(VivintBinarySensorEntity(hub, device))

    if not entities:
        return

    _LOGGER.debug(f"Adding Vivint binary sensors: {entities}")
    async_add_entities(entities, True)


class VivintBinarySensorEntity(BinarySensorEntity):
    """Vivint Binary Sensor."""

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
        return self.device.name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.device.get_root().id}-{self.device.id}"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.device.state == "Opened"

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        equipment_type = self.device.equipment_type
        sensor_type = self.device.sensor_type
        if equipment_type == VivintWirelessSensor.EquipmentType.MOTION:
            return DEVICE_CLASS_MOTION
        elif equipment_type == VivintWirelessSensor.EquipmentType.FREEZE:
            return DEVICE_CLASS_COLD
        elif equipment_type == VivintWirelessSensor.EquipmentType.WATER:
            return DEVICE_CLASS_MOISTURE
        elif equipment_type == VivintWirelessSensor.EquipmentType.TEMPERATURE:
            return DEVICE_CLASS_HEAT
        elif sensor_type in [
            VivintWirelessSensor.SensorType.FIRE,
            VivintWirelessSensor.SensorType.FIRE_WITH_VERIFICATION,
        ]:
            return DEVICE_CLASS_SMOKE
        elif sensor_type == VivintWirelessSensor.SensorType.CARBON_MONOXIDE:
            return DEVICE_CLASS_GAS
        elif "door" in self.name.lower():
            return DEVICE_CLASS_DOOR
        elif "window" in self.name.lower():
            return DEVICE_CLASS_WINDOW
        else:
            return DEVICE_CLASS_SAFETY

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return the device information for a Vivint binary sensor."""
        return {
            "identifiers": {(VIVINT_DOMAIN, self.device.serial_number)},
            "name": self.device.name,
            "manufacturer": self.device.manufacturer,
            "model": self.device.model,
            "sw_version": self.device.software_version,
            "via_device": (VIVINT_DOMAIN, self.device.get_root().id),
        }

"""Support for Vivint binary sensors."""
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_COLD,
    DEVICE_CLASS_DOOR,
    DEVICE_CLASS_GARAGE_DOOR,
    DEVICE_CLASS_GAS,
    DEVICE_CLASS_HEAT,
    DEVICE_CLASS_MOISTURE,
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_SAFETY,
    DEVICE_CLASS_SMOKE,
    DEVICE_CLASS_WINDOW,
    BinarySensorEntity,
)
from vivintpy.devices.wireless_sensor import WirelessSensor
from vivintpy.enums import EquipmentType, SensorType

from .const import DOMAIN
from .hub import VivintEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint binary sensors using config entry."""
    entities = []
    hub = hass.data[DOMAIN][config_entry.entry_id]

    for system in hub.account.systems:
        for alarm_panel in system.alarm_panels:
            for device in alarm_panel.devices:
                if type(device) is WirelessSensor:
                    entities.append(VivintBinarySensorEntity(device=device, hub=hub))

    if not entities:
        return

    async_add_entities(entities, True)


class VivintBinarySensorEntity(VivintEntity, BinarySensorEntity):
    """Vivint Binary Sensor."""

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.device.alarm_panel.id}-{self.device.id}"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.device.is_on

    @property
    def device_class(self):
        """Return the class of this device."""
        equipment_type = self.device.equipment_type

        if equipment_type == EquipmentType.MOTION:
            return DEVICE_CLASS_MOTION

        elif equipment_type == EquipmentType.FREEZE:
            return DEVICE_CLASS_COLD

        elif equipment_type == EquipmentType.WATER:
            return DEVICE_CLASS_MOISTURE

        elif equipment_type == EquipmentType.TEMPERATURE:
            return DEVICE_CLASS_HEAT

        elif equipment_type == EquipmentType.CONTACT:
            sensor_type = self.device.sensor_type

            if sensor_type == SensorType.EXIT_ENTRY_1:
                return (
                    DEVICE_CLASS_GARAGE_DOOR
                    if "TILT" in self.device.equipment_code.name
                    else DEVICE_CLASS_DOOR
                )

            elif sensor_type == SensorType.PERIMETER:
                return (
                    DEVICE_CLASS_SAFETY
                    if "GLASS_BREAK" in self.device.equipment_code.name
                    else DEVICE_CLASS_WINDOW
                )

            elif sensor_type in [SensorType.FIRE, SensorType.FIRE_WITH_VERIFICATION]:
                return DEVICE_CLASS_SMOKE

            elif sensor_type == SensorType.CARBON_MONOXIDE:
                return DEVICE_CLASS_GAS

        else:
            return DEVICE_CLASS_SAFETY

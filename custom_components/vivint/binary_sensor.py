"""Support for Vivint binary sensors."""
from datetime import datetime, timedelta

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
from homeassistant.core import CALLBACK_TYPE, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.util.dt import utcnow
from vivintpy.devices import VivintDevice
from vivintpy.devices.camera import MOTION_DETECTED, Camera
from vivintpy.devices.wireless_sensor import WirelessSensor
from vivintpy.enums import EquipmentType, SensorType

from .const import DOMAIN
from .hub import VivintEntity, VivintHub

MOTION_STOPPED_SECONDS = 30


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint binary sensors using config entry."""
    entities = []
    hub = hass.data[DOMAIN][config_entry.entry_id]

    for system in hub.account.systems:
        for alarm_panel in system.alarm_panels:
            for device in alarm_panel.devices:
                if type(device) is WirelessSensor:
                    entities.append(VivintBinarySensorEntity(device=device, hub=hub))
                elif type(device) is Camera:
                    entities.append(
                        VivintCameraBinarySensorEntity(device=device, hub=hub)
                    )

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


class VivintCameraBinarySensorEntity(VivintEntity, BinarySensorEntity):
    """Vivint Camera Binary Sensor."""

    def __init__(self, device: VivintDevice, hub: VivintHub):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(device=device, hub=hub)
        self._last_motion_event: datetime = None
        self._motion_stopped_callback: CALLBACK_TYPE = None

    @property
    def name(self):
        """Return the name of this entity."""
        return f"{self.device.name} Motion"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.device.alarm_panel.id}-{self.device.id}"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return (
            self._last_motion_event
            and self._last_motion_event >= utcnow() - timedelta(seconds=30)
        )

    @property
    def device_class(self):
        """Return the class of this device."""
        return DEVICE_CLASS_MOTION

    async def async_added_to_hass(self):
        """Register callbacks."""
        await super().async_added_to_hass()
        self.device.on(MOTION_DETECTED, self._motion_callback)

    async def async_will_remove_from_hass(self):
        """Disconnect callbacks."""
        await super().async_will_remove_from_hass()
        self.async_cancel_motion_stopped_callback()

    @callback
    def _motion_callback(self, _):
        """Call motion method."""
        self.async_cancel_motion_stopped_callback()

        self._last_motion_event = utcnow()
        self.async_write_ha_state()

        self._motion_stopped_callback = async_call_later(
            self.hass, MOTION_STOPPED_SECONDS, self.async_motion_stopped_callback
        )

    async def async_motion_stopped_callback(self, *_) -> None:
        """Motion stopped callback."""
        self._motion_stopped_callback = None
        self._last_motion_event = None
        self.async_write_ha_state()

    @callback
    def async_cancel_motion_stopped_callback(self):
        """Clear the motion stopped callback if it has not already fired."""
        if self._motion_stopped_callback is not None:
            self._motion_stopped_callback()
            self._motion_stopped_callback = None

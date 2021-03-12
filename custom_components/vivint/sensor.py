"""Support for Vivint sensors."""
from homeassistant.const import DEVICE_CLASS_BATTERY, PERCENTAGE
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .hub import VivintEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint sensors using config entry."""
    entities = []
    hub = hass.data[DOMAIN][config_entry.entry_id]

    for system in hub.account.systems:
        for alarm_panel in system.alarm_panels:
            for device in alarm_panel.devices:
                if getattr(device, "battery_level", None) is not None:
                    entities.append(VivintSensorEntity(device=device, hub=hub))

    if not entities:
        return

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
        """Return the class of this device."""
        return DEVICE_CLASS_BATTERY

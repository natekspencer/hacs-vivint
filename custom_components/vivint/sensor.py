"""Support for Vivint sensors."""
from vivintpy.devices import VivintDevice

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DEVICE_CLASS_BATTERY, PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .hub import VivintEntity, VivintHub


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up Vivint sensors using config entry."""
    entities = []
    hub: VivintHub = hass.data[DOMAIN][config_entry.entry_id]

    for system in hub.account.systems:
        for alarm_panel in system.alarm_panels:
            for device in alarm_panel.devices:
                if (
                    not device.is_subdevice
                    and getattr(device, "battery_level", None) is not None
                ):
                    entities.append(VivintSensorEntity(device=device, hub=hub))

    if not entities:
        return

    async_add_entities(entities, True)

    @callback
    def async_add_sensor(device: VivintDevice) -> None:
        """Add Vivint sensor."""
        entities: list[VivintSensorEntity] = []
        if (
            not device.is_subdevice
            and getattr(device, "battery_level", None) is not None
        ):
            entities.append(VivintSensorEntity(device=device, hub=hub))

        async_add_entities(entities)

    config_entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"{DOMAIN}_{config_entry.entry_id}_add_{SENSOR_DOMAIN}",
            async_add_sensor,
        )
    )


class VivintSensorEntity(VivintEntity, SensorEntity):
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

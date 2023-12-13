"""Support for Vivint buttons."""
from __future__ import annotations

from vivintpy.devices.alarm_panel import AlarmPanel
from vivintpy.entity import UPDATE

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .hub import VivintBaseEntity, VivintHub

HUB_REBOOT_ENTITY = ButtonEntityDescription(
    key="reboot", device_class=ButtonDeviceClass.RESTART
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Vivint button platform."""
    hub: VivintHub = hass.data[DOMAIN][entry.entry_id]
    entities = [
        VivintButtonEntity(
            device=alarm_panel, hub=hub, entity_description=HUB_REBOOT_ENTITY
        )
        for system in hub.account.systems
        if system.is_admin
        for alarm_panel in system.alarm_panels
    ]
    async_add_entities(entities)


class VivintButtonEntity(VivintBaseEntity, ButtonEntity):
    """A class that describes device button entities."""

    device: AlarmPanel

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self.device._AlarmPanel__panel.data["can_reboot"]

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.device.reboot()

    async def async_added_to_hass(self) -> None:
        """Set up a listener for the entity."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.device._AlarmPanel__panel.on(
                UPDATE, lambda _: self.async_write_ha_state()
            )
        )

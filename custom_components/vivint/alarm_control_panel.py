"""Support for Vivint alarm control panel."""
from __future__ import annotations

from vivintpy.enums import ArmedState

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .hub import VivintEntity

ARMED_STATE_MAP = {
    ArmedState.DISARMED: STATE_ALARM_DISARMED,
    ArmedState.ARMING_AWAY_IN_EXIT_DELAY: STATE_ALARM_ARMING,
    ArmedState.ARMING_STAY_IN_EXIT_DELAY: STATE_ALARM_ARMING,
    ArmedState.ARMED_STAY: STATE_ALARM_ARMED_HOME,
    ArmedState.ARMED_AWAY: STATE_ALARM_ARMED_AWAY,
    ArmedState.ARMED_STAY_IN_ENTRY_DELAY: STATE_ALARM_PENDING,
    ArmedState.ARMED_AWAY_IN_ENTRY_DELAY: STATE_ALARM_PENDING,
    ArmedState.ALARM: STATE_ALARM_TRIGGERED,
    ArmedState.ALARM_FIRE: STATE_ALARM_TRIGGERED,
    ArmedState.DISABLED: STATE_ALARM_DISARMED,
    ArmedState.WALK_TEST: STATE_ALARM_DISARMED,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Vivint alarm control panel using config entry."""
    entities = []
    hub = hass.data[DOMAIN][config_entry.entry_id]

    for system in hub.account.systems:
        for device in system.alarm_panels:
            entities.append(VivintAlarmControlPanelEntity(device=device, hub=hub))

    if not entities:
        return

    async_add_entities(entities, True)


class VivintAlarmControlPanelEntity(VivintEntity, AlarmControlPanelEntity):
    """Vivint Alarm Control Panel."""

    _attr_changed_by = None
    _attr_code_arm_required = False
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
    )

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self.device.id

    @property
    def state(self) -> StateType:
        """Return the state of the alarm control panel."""
        return ARMED_STATE_MAP.get(self.device.state)

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        await self.device.disarm()

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self.device.arm_stay()

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self.device.arm_away()

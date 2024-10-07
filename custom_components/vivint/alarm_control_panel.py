"""Support for Vivint alarm control panel."""

from __future__ import annotations

from vivintpy.devices.alarm_panel import AlarmPanel
from vivintpy.enums import ArmedState

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature as Feature,
    CodeFormat,
)
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

from . import VivintConfigEntry
from .const import CONF_DISARM_CODE
from .hub import VivintEntity, VivintHub

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
    entry: VivintConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Vivint alarm control panel using config entry."""
    entities = []
    hub: VivintHub = entry.runtime_data
    disarm_code = entry.options.get(CONF_DISARM_CODE)

    for system in hub.account.systems:
        for device in system.alarm_panels:
            entities.append(
                VivintAlarmControlPanelEntity(
                    device=device, hub=hub, disarm_code=disarm_code
                )
            )

    if not entities:
        return

    async_add_entities(entities)


class VivintAlarmControlPanelEntity(VivintEntity, AlarmControlPanelEntity):
    """Vivint Alarm Control Panel."""

    device: AlarmPanel

    _attr_changed_by = None
    _attr_code_arm_required = False
    _attr_supported_features = Feature.ARM_HOME | Feature.ARM_AWAY | Feature.TRIGGER

    def __init__(
        self, device: AlarmPanel, hub: VivintHub, disarm_code: str | None
    ) -> None:
        """Create the entity."""
        super().__init__(device, hub)
        self._attr_unique_id = str(self.device.id)
        if disarm_code:
            self._attr_code_format = CodeFormat.NUMBER
            self._disarm_code = disarm_code

    @property
    def state(self) -> StateType:
        """Return the state of the alarm control panel."""
        return ARMED_STATE_MAP.get(self.device.state)

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        if not self.code_format or code == self._disarm_code:
            await self.device.disarm()

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self.device.arm_stay()

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self.device.arm_away()

    async def async_alarm_trigger(self, code: str | None = None) -> None:
        """Send alarm trigger command."""
        await self.device.trigger_alarm()

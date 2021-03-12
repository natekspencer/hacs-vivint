"""Support for Vivint alarm control panel."""
from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity
from homeassistant.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME,
)
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)
from vivintpy.enums import ArmedState

from .const import DOMAIN
from .hub import VivintEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
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

    @property
    def changed_by(self):
        """Last change triggered by."""
        # return self.device.changed_by
        return None

    @property
    def code_arm_required(self):
        """Whether the code is required for arm actions."""
        return False

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return SUPPORT_ALARM_ARM_HOME | SUPPORT_ALARM_ARM_AWAY

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self.device.id

    @property
    def state(self):
        """Return the state of the alarm control panel."""
        arm_state = self.device.get_armed_state()
        if arm_state == ArmedState.DISARMED:
            state = STATE_ALARM_DISARMED
        elif arm_state in [
            ArmedState.ARMED_STAY,
            ArmedState.ARMING_STAY_IN_EXIT_DELAY,
            ArmedState.ARMED_STAY_IN_ENTRY_DELAY,
        ]:
            state = STATE_ALARM_ARMED_HOME
        elif arm_state in [
            ArmedState.ARMED_AWAY,
            ArmedState.ARMING_AWAY_IN_EXIT_DELAY,
            ArmedState.ARMED_AWAY_IN_ENTRY_DELAY,
        ]:
            state = STATE_ALARM_ARMED_AWAY
        elif arm_state in [ArmedState.ALARM, ArmedState.ALARM_FIRE]:
            state = STATE_ALARM_TRIGGERED
        else:
            state = None
        return state

    async def async_alarm_disarm(self, code=None):
        """Send disarm command."""
        await self.device.disarm()

    async def async_alarm_arm_home(self, code=None):
        """Send arm home command."""
        await self.device.arm_stay()

    async def async_alarm_arm_away(self, code=None):
        """Send arm away command."""
        await self.device.arm_away()

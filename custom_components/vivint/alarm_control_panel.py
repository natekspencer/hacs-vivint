"""Support for Vivint alarm control panel."""
from typing import Any, Dict

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
from homeassistant.core import callback
from pyvivintsky import VivintPanel

from . import VivintHub
from .const import _LOGGER, VIVINT_DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint alarm control panel using config entry."""
    entities = []
    hub = hass.data[VIVINT_DOMAIN][config_entry.entry_id]

    panels = hub.api.get_panels()
    for panel in panels:
        entities.append(VivintAlarmControlPanelEntity(hub, panels[panel]))

    if not entities:
        return

    _LOGGER.debug(f"Adding Vivint panels: {entities}")
    async_add_entities(entities, True)


class VivintAlarmControlPanelEntity(AlarmControlPanelEntity):
    """Vivint Alarm Control Panel."""

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
    def changed_by(self):
        """Last change triggered by."""
        return self.device.changed_by

    @property
    def code_arm_required(self):
        """Whether the code is required for arm actions."""
        return False

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return SUPPORT_ALARM_ARM_HOME | SUPPORT_ALARM_ARM_AWAY

    @property
    def name(self):
        """Return the name of this entity."""
        return self.device.name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self.device.id

    @property
    def state(self):
        """Return the state of the alarm control panel."""
        arm_state = self.device.state
        if arm_state == VivintPanel.ArmState.DISARMED:
            state = STATE_ALARM_DISARMED
        elif arm_state in [
            VivintPanel.ArmState.ARMED_STAY,
            VivintPanel.ArmState.ARMING_STAY_IN_EXIT_DELAY,
            VivintPanel.ArmState.ARMED_STAY_IN_ENTRY_DELAY,
        ]:
            state = STATE_ALARM_ARMED_HOME
        elif arm_state in [
            VivintPanel.ArmState.ARMED_AWAY,
            VivintPanel.ArmState.ARMING_AWAY_IN_EXIT_DELAY,
            VivintPanel.ArmState.ARMED_AWAY_IN_ENTRY_DELAY,
        ]:
            state = STATE_ALARM_ARMED_AWAY
        elif arm_state in [VivintPanel.ArmState.ALARM, VivintPanel.ArmState.ALARM_FIRE]:
            state = STATE_ALARM_TRIGGERED
        else:
            state = None
        return state

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return the device information for a Vivint alarm control panel."""
        return {
            "identifiers": {(VIVINT_DOMAIN, self.device.serial_number)},
            "name": self.device.name,
            "manufacturer": self.device.manufacturer,
            "model": self.device.model,
            "sw_version": self.device.software_version,
        }

    async def async_alarm_disarm(self, code=None):
        """Send disarm command."""
        await self.device.set_armed_state(VivintPanel.ArmState.DISARMED)

    async def async_alarm_arm_home(self, code=None):
        """Send arm home command."""
        await self.device.set_armed_state(VivintPanel.ArmState.ARMED_STAY)

    async def async_alarm_arm_away(self, code=None):
        """Send arm away command."""
        await self.device.set_armed_state(VivintPanel.ArmState.ARMED_AWAY)

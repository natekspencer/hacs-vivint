"""Support for Vivint thermostats."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
)
from homeassistant.const import TEMP_CELSIUS
from vivintpy.const import ThermostatAttribute
from vivintpy.devices.thermostat import Thermostat
from vivintpy.enums import OperatingMode

from .const import DOMAIN
from .hub import VivintEntity

_LOGGER = logging.getLogger(__name__)

# Map Vivint HVAC Mode to Home Assistant value
VIVINT_HVAC_MODE_MAP: Dict[int, str] = {
    OperatingMode.OFF: HVAC_MODE_OFF,
    OperatingMode.HEAT: HVAC_MODE_HEAT,
    OperatingMode.COOL: HVAC_MODE_COOL,
    OperatingMode.AUTO: HVAC_MODE_HEAT_COOL,
    OperatingMode.EMERGENCY_HEAT: HVAC_MODE_HEAT,
    OperatingMode.RESUME: HVAC_MODE_AUTO,  # maybe?
    OperatingMode.FAN_ONLY: HVAC_MODE_FAN_ONLY,
    OperatingMode.FURNACE: HVAC_MODE_HEAT,
    OperatingMode.DRY_AIR: HVAC_MODE_DRY,
    OperatingMode.MOIST_AIR: HVAC_MODE_DRY,  # maybe?
    OperatingMode.AUTO_CHANGEOVER: HVAC_MODE_HEAT_COOL,
    OperatingMode.ENERGY_SAVE_HEAT: HVAC_MODE_HEAT,
    OperatingMode.ENERGY_SAVE_COOL: HVAC_MODE_COOL,
    OperatingMode.AWAY: HVAC_MODE_HEAT_COOL,
    OperatingMode.ECO: HVAC_MODE_HEAT_COOL,
}

# HVAC_CURRENT_MAP: Dict[int, str] = {
#     ThermostatOperatingState.IDLE: CURRENT_HVAC_IDLE,
#     ThermostatOperatingState.PENDING_HEAT: CURRENT_HVAC_IDLE,
#     ThermostatOperatingState.HEATING: CURRENT_HVAC_HEAT,
#     ThermostatOperatingState.PENDING_COOL: CURRENT_HVAC_IDLE,
#     ThermostatOperatingState.COOLING: CURRENT_HVAC_COOL,
#     ThermostatOperatingState.FAN_ONLY: CURRENT_HVAC_FAN,
#     ThermostatOperatingState.VENT_ECONOMIZER: CURRENT_HVAC_FAN,
#     ThermostatOperatingState.AUX_HEATING: CURRENT_HVAC_HEAT,
#     ThermostatOperatingState.SECOND_STAGE_HEATING: CURRENT_HVAC_HEAT,
#     ThermostatOperatingState.SECOND_STAGE_COOLING: CURRENT_HVAC_COOL,
#     ThermostatOperatingState.SECOND_STAGE_AUX_HEAT: CURRENT_HVAC_HEAT,
#     ThermostatOperatingState.THIRD_STAGE_AUX_HEAT: CURRENT_HVAC_HEAT,
# }


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint climate using config entry."""
    entities = []
    hub = hass.data[DOMAIN][config_entry.entry_id]

    for system in hub.account.systems:
        for alarm_panel in system.alarm_panels:
            for device in alarm_panel.devices:
                if type(device) is Thermostat:
                    entities.append(VivintClimate(device=device, hub=hub))

    if not entities:
        return

    async_add_entities(entities, True)


class VivintClimate(VivintEntity, ClimateEntity):
    """Vivint Climate."""

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.device.alarm_panel.id}-{self.device.id}"

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
        return self.device.temperature

    @property
    def current_humidity(self) -> Optional[int]:
        """Return the current humidity level."""
        return self.device.humidity

    @property
    def target_temperature(self) -> Optional[float]:
        """Return the temperature we try to reach."""
        return self.device.heat_set_point

    @property
    def target_temperature_high(self) -> Optional[float]:
        """Return the highbound target temperature we try to reach."""
        return self.device.cool_set_point

    @property
    def target_temperature_low(self) -> Optional[float]:
        """Return the lowbound target temperature we try to reach."""
        return self.device.heat_set_point

    @property
    def max_temp(self) -> int:
        """Return the maximum temperature."""
        return self.device.maximum_temperature

    @property
    def min_temp(self) -> int:
        """Return the minimum temperature."""
        return self.device.minimum_temperature

    @property
    def hvac_mode(self) -> str:
        """Return hvac operation ie. heat, cool mode."""
        return VIVINT_HVAC_MODE_MAP.get(
            int(self.device.operating_mode), HVAC_MODE_HEAT_COOL
        )

    # @property
    # def hvac_action(self) -> Optional[str]:
    #     """Return the current running hvac operation if supported."""
    #     return HVAC_CURRENT_MAP.get(int(self._operating_state.value))

    @property
    def hvac_modes(self) -> List[str]:
        """Return the list of available hvac operation modes."""
        return [HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_HEAT_COOL, HVAC_MODE_OFF]

    @property
    def fan_mode(self) -> str:
        """Return the fan mode."""
        return self.device.fan_mode.name

    @property
    def fan_modes(self) -> List[str]:
        """Return the list of available fan modes."""
        return [FAN_AUTO, FAN_LOW, FAN_HIGH]

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return (
            SUPPORT_TARGET_TEMPERATURE
            | SUPPORT_TARGET_TEMPERATURE_RANGE
            | SUPPORT_FAN_MODE
        )

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new target hvac mode."""
        await self.device.set_state(
            **{ThermostatAttribute.OPERATING_MODE: OperatingMode.HEAT}
        )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        _LOGGER.debug(kwargs)

        hvac_mode: Optional[str] = kwargs.get(ATTR_HVAC_MODE)

        if hvac_mode is not None:
            await self.async_set_hvac_mode(hvac_mode)

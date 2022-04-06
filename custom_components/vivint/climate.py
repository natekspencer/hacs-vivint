"""Support for Vivint thermostats."""
from __future__ import annotations

from typing import Any

from vivintpy.const import ThermostatAttribute
from vivintpy.devices.thermostat import Thermostat
from vivintpy.enums import (
    CapabilityCategoryType,
    CapabilityType,
    FanMode,
    OperatingMode,
    OperatingState,
)

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    FAN_AUTO,
    FAN_ON,
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
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .hub import VivintEntity, VivintHub

# Map Vivint HVAC Mode to Home Assistant value
VIVINT_HVAC_MODE_MAP: dict[OperatingMode, str] = {
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

# Map Home Assistant HVAC Mode to Vivint value
VIVINT_HVAC_INV_MODE_MAP: dict[str, OperatingMode] = {
    HVAC_MODE_OFF: OperatingMode.OFF,
    HVAC_MODE_HEAT: OperatingMode.HEAT,
    HVAC_MODE_COOL: OperatingMode.COOL,
    HVAC_MODE_HEAT_COOL: OperatingMode.AUTO,
}

VIVINT_CAPABILITY_FAN_MODE_MAP = {
    CapabilityType.FAN15_MINUTE: FanMode.TIMER_15,
    CapabilityType.FAN30_MINUTE: FanMode.TIMER_30,
    CapabilityType.FAN45_MINUTE: FanMode.TIMER_45,
    CapabilityType.FAN60_MINUTE: FanMode.TIMER_60,
    CapabilityType.FAN120_MINUTE: FanMode.TIMER_120,
    CapabilityType.FAN240_MINUTE: FanMode.TIMER_240,
    CapabilityType.FAN480_MINUTE: FanMode.TIMER_480,
    CapabilityType.FAN960_MINUTE: FanMode.TIMER_960,
}

VIVINT_FAN_MODE_MAP = {
    FanMode.AUTO_LOW: FAN_AUTO,
    FanMode.TIMER_15: "15 minutes",
    FanMode.TIMER_30: "30 minutes",
    FanMode.TIMER_45: "45 minutes",
    FanMode.TIMER_60: "1 hour",
    FanMode.TIMER_120: "2 hours",
    FanMode.TIMER_240: "4 hours",
    FanMode.TIMER_480: "8 hours",
    FanMode.TIMER_720: "12 hours",
    FanMode.TIMER_960: "16 hours",
}

VIVINT_FAN_INV_MODE_MAP: dict[str, FanMode] = {
    v: k for k, v in VIVINT_FAN_MODE_MAP.items()
}

VIVINT_HVAC_STATUS_MAP = {
    OperatingState.IDLE: CURRENT_HVAC_IDLE,
    OperatingState.HEATING: CURRENT_HVAC_HEAT,
    OperatingState.COOLING: CURRENT_HVAC_COOL,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
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

    _attr_temperature_unit = TEMP_CELSIUS
    _attr_supported_features = (
        SUPPORT_TARGET_TEMPERATURE | SUPPORT_TARGET_TEMPERATURE_RANGE | SUPPORT_FAN_MODE
    )

    def __init__(self, device: Thermostat, hub: VivintHub) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(device=device, hub=hub)
        self._fan_modes = [FAN_AUTO, FAN_ON] + [
            VIVINT_FAN_MODE_MAP[VIVINT_CAPABILITY_FAN_MODE_MAP[x]]
            for k, v in device.capabilities.items()
            if k == CapabilityCategoryType.THERMOSTAT
            for x in v
            if x in VIVINT_CAPABILITY_FAN_MODE_MAP
        ]

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self.device.alarm_panel.id}-{self.device.id}"

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.device.temperature

    @property
    def current_humidity(self) -> int | None:
        """Return the current humidity level."""
        return self.device.humidity

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if self.hvac_mode == HVAC_MODE_HEAT:
            return self.device.heat_set_point
        if self.hvac_mode == HVAC_MODE_COOL:
            return self.device.cool_set_point
        return None

    @property
    def target_temperature_high(self) -> float | None:
        """Return the highbound target temperature we try to reach."""
        return (
            None
            if self.hvac_mode != HVAC_MODE_HEAT_COOL
            else self.device.cool_set_point
        )

    @property
    def target_temperature_low(self) -> float | None:
        """Return the lowbound target temperature we try to reach."""
        return (
            None
            if self.hvac_mode != HVAC_MODE_HEAT_COOL
            else self.device.heat_set_point
        )

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
        return VIVINT_HVAC_MODE_MAP.get(self.device.operating_mode, HVAC_MODE_HEAT_COOL)

    @property
    def hvac_action(self) -> str | None:
        """Return the current running hvac operation if supported."""
        return VIVINT_HVAC_STATUS_MAP.get(self.device.operating_mode, CURRENT_HVAC_IDLE)

    @property
    def hvac_modes(self) -> list[str]:
        """Return the list of available hvac operation modes."""
        return [HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_HEAT_COOL, HVAC_MODE_OFF]

    @property
    def fan_mode(self) -> str:
        """Return the fan mode."""
        return VIVINT_FAN_MODE_MAP.get(self.device.fan_mode, FAN_ON)

    @property
    def fan_modes(self) -> list[str]:
        """Return the list of available fan modes."""
        return self._fan_modes

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        await self.device.set_state(
            **{
                ThermostatAttribute.FAN_MODE: VIVINT_FAN_INV_MODE_MAP.get(
                    fan_mode, VIVINT_FAN_INV_MODE_MAP.get(self.fan_modes[-1])
                )
            }
        )

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new target hvac mode."""
        await self.device.set_state(
            **{ThermostatAttribute.OPERATING_MODE: VIVINT_HVAC_INV_MODE_MAP[hvac_mode]}
        )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        low_temp = kwargs.get(ATTR_TARGET_TEMP_LOW)
        high_temp = kwargs.get(ATTR_TARGET_TEMP_HIGH)

        await self.change_target_temperature(
            ThermostatAttribute.COOL_SET_POINT,
            temp if self.hvac_mode == HVAC_MODE_COOL else high_temp,
            self.device.cool_set_point,
        )
        await self.change_target_temperature(
            ThermostatAttribute.HEAT_SET_POINT,
            temp if self.hvac_mode == HVAC_MODE_HEAT else low_temp,
            self.device.heat_set_point,
        )

    async def change_target_temperature(
        self, attribute: str, target: float, current: float
    ) -> bool:
        """Change target temperature."""
        if target is not None and abs(target - current) >= 0.5:
            await self.device.set_state(**{attribute: target})

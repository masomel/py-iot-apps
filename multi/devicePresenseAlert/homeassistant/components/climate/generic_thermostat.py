"""
Adds support for generic thermostat units.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/climate.generic_thermostat/
"""
import logging

import voluptuous as vol

from homeassistant.components import switch
from homeassistant.components.climate import (
    STATE_HEAT, STATE_COOL, STATE_IDLE, ClimateDevice, PLATFORM_SCHEMA)
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT, STATE_ON, STATE_OFF, ATTR_TEMPERATURE)
from homeassistant.helpers import condition
from homeassistant.helpers.event import track_state_change
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['switch', 'sensor']

DEFAULT_TOLERANCE = 0.3
DEFAULT_NAME = 'Generic Thermostat'

CONF_NAME = 'name'
CONF_HEATER = 'heater'
CONF_SENSOR = 'target_sensor'
CONF_MIN_TEMP = 'min_temp'
CONF_MAX_TEMP = 'max_temp'
CONF_TARGET_TEMP = 'target_temp'
CONF_AC_MODE = 'ac_mode'
CONF_MIN_DUR = 'min_cycle_duration'
CONF_TOLERANCE = 'tolerance'


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HEATER): cv.entity_id,
    vol.Required(CONF_SENSOR): cv.entity_id,
    vol.Optional(CONF_AC_MODE): cv.boolean,
    vol.Optional(CONF_MAX_TEMP): vol.Coerce(float),
    vol.Optional(CONF_MIN_DUR): vol.All(cv.time_period, cv.positive_timedelta),
    vol.Optional(CONF_MIN_TEMP): vol.Coerce(float),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TOLERANCE, default=DEFAULT_TOLERANCE): vol.Coerce(float),
    vol.Optional(CONF_TARGET_TEMP): vol.Coerce(float),
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the generic thermostat."""
    name = config.get(CONF_NAME)
    heater_entity_id = config.get(CONF_HEATER)
    sensor_entity_id = config.get(CONF_SENSOR)
    min_temp = config.get(CONF_MIN_TEMP)
    max_temp = config.get(CONF_MAX_TEMP)
    target_temp = config.get(CONF_TARGET_TEMP)
    ac_mode = config.get(CONF_AC_MODE)
    min_cycle_duration = config.get(CONF_MIN_DUR)
    tolerance = config.get(CONF_TOLERANCE)

    add_devices([GenericThermostat(
        hass, name, heater_entity_id, sensor_entity_id, min_temp, max_temp,
        target_temp, ac_mode, min_cycle_duration, tolerance)])


class GenericThermostat(ClimateDevice):
    """Representation of a GenericThermostat device."""

    def __init__(self, hass, name, heater_entity_id, sensor_entity_id,
                 min_temp, max_temp, target_temp, ac_mode, min_cycle_duration,
                 tolerance):
        """Initialize the thermostat."""
        self.hass = hass
        self._name = name
        self.heater_entity_id = heater_entity_id
        self.ac_mode = ac_mode
        self.min_cycle_duration = min_cycle_duration
        self._tolerance = tolerance

        self._active = False
        self._cur_temp = None
        self._min_temp = min_temp
        self._max_temp = max_temp
        self._target_temp = target_temp
        self._unit = hass.config.units.temperature_unit

        track_state_change(hass, sensor_entity_id, self._sensor_changed)

        sensor_state = hass.states.get(sensor_entity_id)
        if sensor_state:
            self._update_temp(sensor_state)

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def current_temperature(self):
        """Return the sensor temperature."""
        return self._cur_temp

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        if self.ac_mode:
            cooling = self._active and self._is_device_active
            return STATE_COOL if cooling else STATE_IDLE
        else:
            heating = self._active and self._is_device_active
            return STATE_HEAT if heating else STATE_IDLE

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temp

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        self._target_temp = temperature
        self._control_heating()
        self.update_ha_state()

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        # pylint: disable=no-member
        if self._min_temp:
            return self._min_temp
        else:
            # get default temp from super class
            return ClimateDevice.min_temp.fget(self)

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        # pylint: disable=no-member
        if self._max_temp:
            return self._max_temp
        else:
            # Get default temp from super class
            return ClimateDevice.max_temp.fget(self)

    def _sensor_changed(self, entity_id, old_state, new_state):
        """Called when temperature changes."""
        if new_state is None:
            return

        self._update_temp(new_state)
        self._control_heating()
        self.schedule_update_ha_state()

    def _update_temp(self, state):
        """Update thermostat with latest state from sensor."""
        unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)

        try:
            self._cur_temp = self.hass.config.units.temperature(
                float(state.state), unit)
        except ValueError as ex:
            _LOGGER.error('Unable to update from sensor: %s', ex)

    def _control_heating(self):
        """Check if we need to turn heating on or off."""
        if not self._active and None not in (self._cur_temp,
                                             self._target_temp):
            self._active = True
            _LOGGER.info('Obtained current and target temperature. '
                         'Generic thermostat active.')

        if not self._active:
            return

        if self.min_cycle_duration:
            if self._is_device_active:
                current_state = STATE_ON
            else:
                current_state = STATE_OFF
            long_enough = condition.state(self.hass, self.heater_entity_id,
                                          current_state,
                                          self.min_cycle_duration)
            if not long_enough:
                return

        if self.ac_mode:
            is_cooling = self._is_device_active
            if is_cooling:
                too_cold = self._target_temp - self._cur_temp > self._tolerance
                if too_cold:
                    _LOGGER.info('Turning off AC %s', self.heater_entity_id)
                    switch.turn_off(self.hass, self.heater_entity_id)
            else:
                too_hot = self._cur_temp - self._target_temp > self._tolerance
                if too_hot:
                    _LOGGER.info('Turning on AC %s', self.heater_entity_id)
                    switch.turn_on(self.hass, self.heater_entity_id)
        else:
            is_heating = self._is_device_active
            if is_heating:
                too_hot = self._cur_temp - self._target_temp > self._tolerance
                if too_hot:
                    _LOGGER.info('Turning off heater %s',
                                 self.heater_entity_id)
                    switch.turn_off(self.hass, self.heater_entity_id)
            else:
                too_cold = self._target_temp - self._cur_temp > self._tolerance
                if too_cold:
                    _LOGGER.info('Turning on heater %s', self.heater_entity_id)
                    switch.turn_on(self.hass, self.heater_entity_id)

    @property
    def _is_device_active(self):
        """If the toggleable device is currently active."""
        return switch.is_on(self.hass, self.heater_entity_id)

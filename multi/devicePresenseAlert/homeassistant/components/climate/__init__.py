"""
Provides functionality to interact with climate devices.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/climate/
"""
import asyncio
from datetime import timedelta
import logging
import os
import functools as ft
from numbers import Number

import voluptuous as vol

from homeassistant.config import load_yaml_config_file
from homeassistant.util.temperature import convert as convert_temperature
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA  # noqa
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    ATTR_ENTITY_ID, ATTR_TEMPERATURE, STATE_ON, STATE_OFF, STATE_UNKNOWN,
    TEMP_CELSIUS)

DOMAIN = "climate"

ENTITY_ID_FORMAT = DOMAIN + ".{}"
SCAN_INTERVAL = timedelta(seconds=60)

SERVICE_SET_AWAY_MODE = "set_away_mode"
SERVICE_SET_AUX_HEAT = "set_aux_heat"
SERVICE_SET_TEMPERATURE = "set_temperature"
SERVICE_SET_FAN_MODE = "set_fan_mode"
SERVICE_SET_OPERATION_MODE = "set_operation_mode"
SERVICE_SET_SWING_MODE = "set_swing_mode"
SERVICE_SET_HUMIDITY = "set_humidity"

STATE_HEAT = "heat"
STATE_COOL = "cool"
STATE_IDLE = "idle"
STATE_AUTO = "auto"
STATE_DRY = "dry"
STATE_FAN_ONLY = "fan_only"

ATTR_CURRENT_TEMPERATURE = "current_temperature"
ATTR_MAX_TEMP = "max_temp"
ATTR_MIN_TEMP = "min_temp"
ATTR_TARGET_TEMP_HIGH = "target_temp_high"
ATTR_TARGET_TEMP_LOW = "target_temp_low"
ATTR_AWAY_MODE = "away_mode"
ATTR_AUX_HEAT = "aux_heat"
ATTR_FAN_MODE = "fan_mode"
ATTR_FAN_LIST = "fan_list"
ATTR_CURRENT_HUMIDITY = "current_humidity"
ATTR_HUMIDITY = "humidity"
ATTR_MAX_HUMIDITY = "max_humidity"
ATTR_MIN_HUMIDITY = "min_humidity"
ATTR_OPERATION_MODE = "operation_mode"
ATTR_OPERATION_LIST = "operation_list"
ATTR_SWING_MODE = "swing_mode"
ATTR_SWING_LIST = "swing_list"

# The degree of precision for each platform
PRECISION_WHOLE = 1
PRECISION_HALVES = 0.5
PRECISION_TENTHS = 0.1

CONVERTIBLE_ATTRIBUTE = [
    ATTR_TEMPERATURE,
    ATTR_TARGET_TEMP_LOW,
    ATTR_TARGET_TEMP_HIGH,
]

_LOGGER = logging.getLogger(__name__)

SET_AWAY_MODE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_AWAY_MODE): cv.boolean,
})
SET_AUX_HEAT_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_AUX_HEAT): cv.boolean,
})
SET_TEMPERATURE_SCHEMA = vol.Schema({
    vol.Exclusive(ATTR_TEMPERATURE, 'temperature'): vol.Coerce(float),
    vol.Inclusive(ATTR_TARGET_TEMP_HIGH, 'temperature'): vol.Coerce(float),
    vol.Inclusive(ATTR_TARGET_TEMP_LOW, 'temperature'): vol.Coerce(float),
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Optional(ATTR_OPERATION_MODE): cv.string,
})
SET_FAN_MODE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_FAN_MODE): cv.string,
})
SET_OPERATION_MODE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_OPERATION_MODE): cv.string,
})
SET_HUMIDITY_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_HUMIDITY): vol.Coerce(float),
})
SET_SWING_MODE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_SWING_MODE): cv.string,
})


def set_away_mode(hass, away_mode, entity_id=None):
    """Turn all or specified climate devices away mode on."""
    data = {
        ATTR_AWAY_MODE: away_mode
    }

    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id

    hass.services.call(DOMAIN, SERVICE_SET_AWAY_MODE, data)


def set_aux_heat(hass, aux_heat, entity_id=None):
    """Turn all or specified climate devices auxillary heater on."""
    data = {
        ATTR_AUX_HEAT: aux_heat
    }

    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id

    hass.services.call(DOMAIN, SERVICE_SET_AUX_HEAT, data)


def set_temperature(hass, temperature=None, entity_id=None,
                    target_temp_high=None, target_temp_low=None,
                    operation_mode=None):
    """Set new target temperature."""
    kwargs = {
        key: value for key, value in [
            (ATTR_TEMPERATURE, temperature),
            (ATTR_TARGET_TEMP_HIGH, target_temp_high),
            (ATTR_TARGET_TEMP_LOW, target_temp_low),
            (ATTR_ENTITY_ID, entity_id),
            (ATTR_OPERATION_MODE, operation_mode)
        ] if value is not None
    }
    _LOGGER.debug("set_temperature start data=%s", kwargs)
    hass.services.call(DOMAIN, SERVICE_SET_TEMPERATURE, kwargs)


def set_humidity(hass, humidity, entity_id=None):
    """Set new target humidity."""
    data = {ATTR_HUMIDITY: humidity}

    if entity_id is not None:
        data[ATTR_ENTITY_ID] = entity_id

    hass.services.call(DOMAIN, SERVICE_SET_HUMIDITY, data)


def set_fan_mode(hass, fan, entity_id=None):
    """Set all or specified climate devices fan mode on."""
    data = {ATTR_FAN_MODE: fan}

    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id

    hass.services.call(DOMAIN, SERVICE_SET_FAN_MODE, data)


def set_operation_mode(hass, operation_mode, entity_id=None):
    """Set new target operation mode."""
    data = {ATTR_OPERATION_MODE: operation_mode}

    if entity_id is not None:
        data[ATTR_ENTITY_ID] = entity_id

    hass.services.call(DOMAIN, SERVICE_SET_OPERATION_MODE, data)


def set_swing_mode(hass, swing_mode, entity_id=None):
    """Set new target swing mode."""
    data = {ATTR_SWING_MODE: swing_mode}

    if entity_id is not None:
        data[ATTR_ENTITY_ID] = entity_id

    hass.services.call(DOMAIN, SERVICE_SET_SWING_MODE, data)


@asyncio.coroutine
def async_setup(hass, config):
    """Setup climate devices."""
    component = EntityComponent(_LOGGER, DOMAIN, hass, SCAN_INTERVAL)
    yield from component.async_setup(config)

    descriptions = yield from hass.loop.run_in_executor(
        None, load_yaml_config_file,
        os.path.join(os.path.dirname(__file__), 'services.yaml'))

    @asyncio.coroutine
    def _async_update_climate(target_climate):
        """Update climate entity after service stuff."""
        update_tasks = []
        for climate in target_climate:
            if not climate.should_poll:
                continue

            update_coro = hass.loop.create_task(
                climate.async_update_ha_state(True))
            if hasattr(climate, 'async_update'):
                update_tasks.append(update_coro)
            else:
                yield from update_coro

        if update_tasks:
            yield from asyncio.wait(update_tasks, loop=hass.loop)

    @asyncio.coroutine
    def async_away_mode_set_service(service):
        """Set away mode on target climate devices."""
        target_climate = component.async_extract_from_service(service)

        away_mode = service.data.get(ATTR_AWAY_MODE)

        if away_mode is None:
            _LOGGER.error(
                "Received call to %s without attribute %s",
                SERVICE_SET_AWAY_MODE, ATTR_AWAY_MODE)
            return

        for climate in target_climate:
            if away_mode:
                yield from climate.async_turn_away_mode_on()
            else:
                yield from climate.async_turn_away_mode_off()

        yield from _async_update_climate(target_climate)

    hass.services.async_register(
        DOMAIN, SERVICE_SET_AWAY_MODE, async_away_mode_set_service,
        descriptions.get(SERVICE_SET_AWAY_MODE),
        schema=SET_AWAY_MODE_SCHEMA)

    @asyncio.coroutine
    def async_aux_heat_set_service(service):
        """Set auxillary heater on target climate devices."""
        target_climate = component.async_extract_from_service(service)

        aux_heat = service.data.get(ATTR_AUX_HEAT)

        if aux_heat is None:
            _LOGGER.error(
                "Received call to %s without attribute %s",
                SERVICE_SET_AUX_HEAT, ATTR_AUX_HEAT)
            return

        for climate in target_climate:
            if aux_heat:
                yield from climate.async_turn_aux_heat_on()
            else:
                yield from climate.async_turn_aux_heat_off()

        yield from _async_update_climate(target_climate)

    hass.services.async_register(
        DOMAIN, SERVICE_SET_AUX_HEAT, async_aux_heat_set_service,
        descriptions.get(SERVICE_SET_AUX_HEAT),
        schema=SET_AUX_HEAT_SCHEMA)

    @asyncio.coroutine
    def async_temperature_set_service(service):
        """Set temperature on the target climate devices."""
        target_climate = component.async_extract_from_service(service)

        for climate in target_climate:
            kwargs = {}
            for value, temp in list(service.data.items()):
                if value in CONVERTIBLE_ATTRIBUTE:
                    kwargs[value] = convert_temperature(
                        temp,
                        hass.config.units.temperature_unit,
                        climate.temperature_unit
                    )
                else:
                    kwargs[value] = temp

            yield from climate.async_set_temperature(**kwargs)

        yield from _async_update_climate(target_climate)

    hass.services.async_register(
        DOMAIN, SERVICE_SET_TEMPERATURE, async_temperature_set_service,
        descriptions.get(SERVICE_SET_TEMPERATURE),
        schema=SET_TEMPERATURE_SCHEMA)

    @asyncio.coroutine
    def async_humidity_set_service(service):
        """Set humidity on the target climate devices."""
        target_climate = component.async_extract_from_service(service)

        humidity = service.data.get(ATTR_HUMIDITY)

        if humidity is None:
            _LOGGER.error(
                "Received call to %s without attribute %s",
                SERVICE_SET_HUMIDITY, ATTR_HUMIDITY)
            return

        for climate in target_climate:
            yield from climate.async_set_humidity(humidity)

        yield from _async_update_climate(target_climate)

    hass.services.async_register(
        DOMAIN, SERVICE_SET_HUMIDITY, async_humidity_set_service,
        descriptions.get(SERVICE_SET_HUMIDITY),
        schema=SET_HUMIDITY_SCHEMA)

    @asyncio.coroutine
    def async_fan_mode_set_service(service):
        """Set fan mode on target climate devices."""
        target_climate = component.async_extract_from_service(service)

        fan = service.data.get(ATTR_FAN_MODE)

        if fan is None:
            _LOGGER.error(
                "Received call to %s without attribute %s",
                SERVICE_SET_FAN_MODE, ATTR_FAN_MODE)
            return

        for climate in target_climate:
            yield from climate.async_set_fan_mode(fan)

        yield from _async_update_climate(target_climate)

    hass.services.async_register(
        DOMAIN, SERVICE_SET_FAN_MODE, async_fan_mode_set_service,
        descriptions.get(SERVICE_SET_FAN_MODE),
        schema=SET_FAN_MODE_SCHEMA)

    @asyncio.coroutine
    def async_operation_set_service(service):
        """Set operating mode on the target climate devices."""
        target_climate = component.async_extract_from_service(service)

        operation_mode = service.data.get(ATTR_OPERATION_MODE)

        if operation_mode is None:
            _LOGGER.error(
                "Received call to %s without attribute %s",
                SERVICE_SET_OPERATION_MODE, ATTR_OPERATION_MODE)
            return

        for climate in target_climate:
            yield from climate.async_set_operation_mode(operation_mode)

        yield from _async_update_climate(target_climate)

    hass.services.async_register(
        DOMAIN, SERVICE_SET_OPERATION_MODE, async_operation_set_service,
        descriptions.get(SERVICE_SET_OPERATION_MODE),
        schema=SET_OPERATION_MODE_SCHEMA)

    @asyncio.coroutine
    def async_swing_set_service(service):
        """Set swing mode on the target climate devices."""
        target_climate = component.async_extract_from_service(service)

        swing_mode = service.data.get(ATTR_SWING_MODE)

        if swing_mode is None:
            _LOGGER.error(
                "Received call to %s without attribute %s",
                SERVICE_SET_SWING_MODE, ATTR_SWING_MODE)
            return

        for climate in target_climate:
            yield from climate.async_set_swing_mode(swing_mode)

        yield from _async_update_climate(target_climate)

    hass.services.async_register(
        DOMAIN, SERVICE_SET_SWING_MODE, async_swing_set_service,
        descriptions.get(SERVICE_SET_SWING_MODE),
        schema=SET_SWING_MODE_SCHEMA)

    return True


class ClimateDevice(Entity):
    """Representation of a climate device."""

    # pylint: disable=no-self-use
    @property
    def state(self):
        """Return the current state."""
        if self.current_operation:
            return self.current_operation
        else:
            return STATE_UNKNOWN

    @property
    def precision(self):
        """Return the precision of the system."""
        if self.unit_of_measurement == TEMP_CELSIUS:
            return PRECISION_TENTHS
        else:
            return PRECISION_WHOLE

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data = {
            ATTR_CURRENT_TEMPERATURE:
            self._convert_for_display(self.current_temperature),
            ATTR_MIN_TEMP: self._convert_for_display(self.min_temp),
            ATTR_MAX_TEMP: self._convert_for_display(self.max_temp),
            ATTR_TEMPERATURE:
            self._convert_for_display(self.target_temperature),
        }
        target_temp_high = self.target_temperature_high
        if target_temp_high is not None:
            data[ATTR_TARGET_TEMP_HIGH] = self._convert_for_display(
                self.target_temperature_high)
            data[ATTR_TARGET_TEMP_LOW] = self._convert_for_display(
                self.target_temperature_low)

        humidity = self.target_humidity
        if humidity is not None:
            data[ATTR_HUMIDITY] = humidity
            data[ATTR_CURRENT_HUMIDITY] = self.current_humidity
            data[ATTR_MIN_HUMIDITY] = self.min_humidity
            data[ATTR_MAX_HUMIDITY] = self.max_humidity

        fan_mode = self.current_fan_mode
        if fan_mode is not None:
            data[ATTR_FAN_MODE] = fan_mode
            if self.fan_list:
                data[ATTR_FAN_LIST] = self.fan_list

        operation_mode = self.current_operation
        if operation_mode is not None:
            data[ATTR_OPERATION_MODE] = operation_mode
            if self.operation_list:
                data[ATTR_OPERATION_LIST] = self.operation_list

        swing_mode = self.current_swing_mode
        if swing_mode is not None:
            data[ATTR_SWING_MODE] = swing_mode
            if self.swing_list:
                data[ATTR_SWING_LIST] = self.swing_list

        is_away = self.is_away_mode_on
        if is_away is not None:
            data[ATTR_AWAY_MODE] = STATE_ON if is_away else STATE_OFF

        is_aux_heat = self.is_aux_heat_on
        if is_aux_heat is not None:
            data[ATTR_AUX_HEAT] = STATE_ON if is_aux_heat else STATE_OFF

        return data

    @property
    def unit_of_measurement(self):
        """The unit of measurement to display."""
        return self.hass.config.units.temperature_unit

    @property
    def temperature_unit(self):
        """The unit of measurement used by the platform."""
        raise NotImplementedError

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return None

    @property
    def target_humidity(self):
        """Return the humidity we try to reach."""
        return None

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        return None

    @property
    def operation_list(self):
        """List of available operation modes."""
        return None

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return None

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return None

    @property
    def target_temperature_high(self):
        """Return the highbound target temperature we try to reach."""
        return None

    @property
    def target_temperature_low(self):
        """Return the lowbound target temperature we try to reach."""
        return None

    @property
    def is_away_mode_on(self):
        """Return true if away mode is on."""
        return None

    @property
    def is_aux_heat_on(self):
        """Return true if aux heater."""
        return None

    @property
    def current_fan_mode(self):
        """Return the fan setting."""
        return None

    @property
    def fan_list(self):
        """List of available fan modes."""
        return None

    @property
    def current_swing_mode(self):
        """Return the fan setting."""
        return None

    @property
    def swing_list(self):
        """List of available swing modes."""
        return None

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        raise NotImplementedError()

    def async_set_temperature(self, **kwargs):
        """Set new target temperature.

        This method must be run in the event loop and returns a coroutine.
        """
        return self.hass.loop.run_in_executor(
            None, ft.partial(self.set_temperature, **kwargs))

    def set_humidity(self, humidity):
        """Set new target humidity."""
        raise NotImplementedError()

    def async_set_humidity(self, humidity):
        """Set new target humidity.

        This method must be run in the event loop and returns a coroutine.
        """
        return self.hass.loop.run_in_executor(
            None, self.set_humidity, humidity)

    def set_fan_mode(self, fan):
        """Set new target fan mode."""
        raise NotImplementedError()

    def async_set_fan_mode(self, fan):
        """Set new target fan mode.

        This method must be run in the event loop and returns a coroutine.
        """
        return self.hass.loop.run_in_executor(
            None, self.set_fan_mode, fan)

    def set_operation_mode(self, operation_mode):
        """Set new target operation mode."""
        raise NotImplementedError()

    def async_set_operation_mode(self, operation_mode):
        """Set new target operation mode.

        This method must be run in the event loop and returns a coroutine.
        """
        return self.hass.loop.run_in_executor(
            None, self.set_operation_mode, operation_mode)

    def set_swing_mode(self, swing_mode):
        """Set new target swing operation."""
        raise NotImplementedError()

    def async_set_swing_mode(self, swing_mode):
        """Set new target swing operation.

        This method must be run in the event loop and returns a coroutine.
        """
        return self.hass.loop.run_in_executor(
            None, self.set_swing_mode, swing_mode)

    def turn_away_mode_on(self):
        """Turn away mode on."""
        raise NotImplementedError()

    def async_turn_away_mode_on(self):
        """Turn away mode on.

        This method must be run in the event loop and returns a coroutine.
        """
        return self.hass.loop.run_in_executor(
            None, self.turn_away_mode_on)

    def turn_away_mode_off(self):
        """Turn away mode off."""
        raise NotImplementedError()

    def async_turn_away_mode_off(self):
        """Turn away mode off.

        This method must be run in the event loop and returns a coroutine.
        """
        return self.hass.loop.run_in_executor(
            None, self.turn_away_mode_off)

    def turn_aux_heat_on(self):
        """Turn auxillary heater on."""
        raise NotImplementedError()

    def async_turn_aux_heat_on(self):
        """Turn auxillary heater on.

        This method must be run in the event loop and returns a coroutine.
        """
        return self.hass.loop.run_in_executor(
            None, self.turn_aux_heat_on)

    def turn_aux_heat_off(self):
        """Turn auxillary heater off."""
        raise NotImplementedError()

    def async_turn_aux_heat_off(self):
        """Turn auxillary heater off.

        This method must be run in the event loop and returns a coroutine.
        """
        return self.hass.loop.run_in_executor(
            None, self.turn_aux_heat_off)

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return convert_temperature(7, TEMP_CELSIUS, self.temperature_unit)

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return convert_temperature(35, TEMP_CELSIUS, self.temperature_unit)

    @property
    def min_humidity(self):
        """Return the minimum humidity."""
        return 30

    @property
    def max_humidity(self):
        """Return the maximum humidity."""
        return 99

    def _convert_for_display(self, temp):
        """Convert temperature into preferred units for display purposes."""
        if (temp is None or not isinstance(temp, Number) or
                self.temperature_unit == self.unit_of_measurement):
            return temp

        value = convert_temperature(temp, self.temperature_unit,
                                    self.unit_of_measurement)

        # Round in the units appropriate
        if self.precision == PRECISION_HALVES:
            return round(value * 2) / 2.0
        elif self.precision == PRECISION_TENTHS:
            return round(value, 1)
        else:
            # PRECISION_WHOLE as a fall back
            return round(value)

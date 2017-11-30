"""
Support for showing values from Dweet.io.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.dweet/
"""
import json
import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME, CONF_VALUE_TEMPLATE, STATE_UNKNOWN, CONF_UNIT_OF_MEASUREMENT)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

REQUIREMENTS = ['dweepy==0.2.0']

_LOGGER = logging.getLogger(__name__)

CONF_DEVICE = 'device'

DEFAULT_NAME = 'Dweet.io Sensor'

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICE): cv.string,
    vol.Required(CONF_VALUE_TEMPLATE): cv.template,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
})


# pylint: disable=unused-variable, too-many-function-args
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Dweet sensor."""
    import dweepy

    name = config.get(CONF_NAME)
    device = config.get(CONF_DEVICE)
    value_template = config.get(CONF_VALUE_TEMPLATE)
    unit = config.get(CONF_UNIT_OF_MEASUREMENT)
    value_template.hass = hass
    try:
        content = json.dumps(dweepy.get_latest_dweet_for(device)[0]['content'])
    except dweepy.DweepyError:
        _LOGGER.error("Device/thing '%s' could not be found", device)
        return False

    if value_template.render_with_possible_json_value(content) == '':
        _LOGGER.error("'%s' was not found", value_template)
        return False

    dweet = DweetData(device)

    add_devices([DweetSensor(hass, dweet, name, value_template, unit)])


class DweetSensor(Entity):
    """Representation of a Dweet sensor."""

    def __init__(self, hass, dweet, name, value_template, unit_of_measurement):
        """Initialize the sensor."""
        self.hass = hass
        self.dweet = dweet
        self._name = name
        self._value_template = value_template
        self._state = STATE_UNKNOWN
        self._unit_of_measurement = unit_of_measurement
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement

    @property
    def state(self):
        """Return the state."""
        if self.dweet.data is None:
            return STATE_UNKNOWN
        else:
            values = json.dumps(self.dweet.data[0]['content'])
            value = self._value_template.render_with_possible_json_value(
                values)
            return value

    def update(self):
        """Get the latest data from REST API."""
        self.dweet.update()


class DweetData(object):
    """The class for handling the data retrieval."""

    def __init__(self, device):
        """Initialize the sensor."""
        self._device = device
        self.data = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data from Dweet.io."""
        import dweepy

        try:
            self.data = dweepy.get_latest_dweet_for(self._device)
        except dweepy.DweepyError:
            _LOGGER.error("Device '%s' could not be found", self._device)
            self.data = None

"""
Support for an exposed aREST RESTful API of a device.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.arest/
"""
import logging
from datetime import timedelta

import requests
import voluptuous as vol

from homeassistant.components.binary_sensor import (
    BinarySensorDevice, PLATFORM_SCHEMA, SENSOR_CLASSES_SCHEMA)
from homeassistant.const import (
    CONF_RESOURCE, CONF_PIN, CONF_NAME, CONF_SENSOR_CLASS)
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_RESOURCE): cv.url,
    vol.Optional(CONF_NAME): cv.string,
    vol.Required(CONF_PIN): cv.string,
    vol.Optional(CONF_SENSOR_CLASS): SENSOR_CLASSES_SCHEMA,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the aREST binary sensor."""
    resource = config.get(CONF_RESOURCE)
    pin = config.get(CONF_PIN)
    sensor_class = config.get(CONF_SENSOR_CLASS)

    try:
        response = requests.get(resource, timeout=10).json()
    except requests.exceptions.MissingSchema:
        _LOGGER.error('Missing resource or schema in configuration. '
                      'Add http:// to your URL.')
        return False
    except requests.exceptions.ConnectionError:
        _LOGGER.error('No route to device at %s. '
                      'Please check the IP address in the configuration file.',
                      resource)
        return False

    arest = ArestData(resource, pin)

    add_devices([ArestBinarySensor(
        arest, resource, config.get(CONF_NAME, response[CONF_NAME]),
        sensor_class, pin)])


class ArestBinarySensor(BinarySensorDevice):
    """Implement an aREST binary sensor for a pin."""

    def __init__(self, arest, resource, name, sensor_class, pin):
        """Initialize the aREST device."""
        self.arest = arest
        self._resource = resource
        self._name = name
        self._sensor_class = sensor_class
        self._pin = pin
        self.update()

        if self._pin is not None:
            request = requests.get('{}/mode/{}/i'.format
                                   (self._resource, self._pin), timeout=10)
            if request.status_code is not 200:
                _LOGGER.error("Can't set mode. Is device offline?")

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return self._name

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return bool(self.arest.data.get('state'))

    @property
    def sensor_class(self):
        """Return the class of this sensor."""
        return self._sensor_class

    def update(self):
        """Get the latest data from aREST API."""
        self.arest.update()


class ArestData(object):
    """Class for handling the data retrieval for pins."""

    def __init__(self, resource, pin):
        """Initialize the aREST data object."""
        self._resource = resource
        self._pin = pin
        self.data = {}

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data from aREST device."""
        try:
            response = requests.get('{}/digital/{}'.format(
                self._resource, self._pin), timeout=10)
            self.data = {'state': response.json()['return_value']}
        except requests.exceptions.ConnectionError:
            _LOGGER.error("No route to device '%s'. Is device offline?",
                          self._resource)

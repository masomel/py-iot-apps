"""
Support for Xiaomi Mi Flora BLE plant sensor.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.miflora/
"""
from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle
from homeassistant.const import (
    CONF_MONITORED_CONDITIONS, CONF_NAME, CONF_MAC)

REQUIREMENTS = ['miflora==0.1.14']

_LOGGER = logging.getLogger(__name__)

CONF_CACHE = 'cache_value'
CONF_FORCE_UPDATE = 'force_update'
CONF_MEDIAN = 'median'
CONF_RETRIES = 'retries'
CONF_TIMEOUT = 'timeout'

DEFAULT_FORCE_UPDATE = False
DEFAULT_MEDIAN = 3
DEFAULT_NAME = 'Mi Flora'
DEFAULT_RETRIES = 2
DEFAULT_TIMEOUT = 10

UPDATE_INTERVAL = 1200
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=UPDATE_INTERVAL)

# Sensor types are defined like: Name, units
SENSOR_TYPES = {
    'temperature': ['Temperature', '°C'],
    'light': ['Light intensity', 'lux'],
    'moisture': ['Moisture', '%'],
    'conductivity': ['Conductivity', 'µS/cm'],
    'battery': ['Battery', '%'],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAC): cv.string,
    vol.Required(CONF_MONITORED_CONDITIONS):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_MEDIAN, default=DEFAULT_MEDIAN): cv.positive_int,
    vol.Optional(CONF_FORCE_UPDATE, default=DEFAULT_FORCE_UPDATE): cv.boolean,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    vol.Optional(CONF_RETRIES, default=DEFAULT_RETRIES): cv.positive_int,
    vol.Optional(CONF_CACHE, default=UPDATE_INTERVAL): cv.positive_int,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the MiFlora sensor."""
    from .miflora import miflora_poller

    cache = config.get(CONF_CACHE)
    poller = miflora_poller.MiFloraPoller(
        config.get(CONF_MAC), cache_timeout=cache)
    force_update = config.get(CONF_FORCE_UPDATE)
    median = config.get(CONF_MEDIAN)
    poller.ble_timeout = config.get(CONF_TIMEOUT)
    poller.retries = config.get(CONF_RETRIES)

    devs = []

    for parameter in config[CONF_MONITORED_CONDITIONS]:
        name = SENSOR_TYPES[parameter][0]
        unit = SENSOR_TYPES[parameter][1]

        prefix = config.get(CONF_NAME)
        if len(prefix) > 0:
            name = "{} {}".format(prefix, name)

        devs.append(MiFloraSensor(
            poller, parameter, name, unit, force_update, median))

    add_devices(devs)


class MiFloraSensor(Entity):
    """Implementing the MiFlora sensor."""

    def __init__(self, poller, parameter, name, unit, force_update, median):
        """Initialize the sensor."""
        self.poller = poller
        self.parameter = parameter
        self._unit = unit
        self._name = name
        self._state = None
        self.data = []
        self._force_update = force_update
        # Median is used to filter out outliers. median of 3 will filter
        # single outliers, while  median of 5 will filter double outliers
        # Use median_count = 1 if no filtering is required.
        self.median_count = median

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return self._unit

    @property
    def force_update(self):
        """Force update."""
        return self._force_update

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """
        Update current conditions.

        This uses a rolling median over 3 values to filter out outliers.
        """
        try:
            _LOGGER.debug("Polling data for %s", self.name)
            data = self.poller.parameter_value(self.parameter)
        except IOError as ioerr:
            _LOGGER.info("Polling error %s", ioerr)
            data = None
            return

        if data is not None:
            _LOGGER.debug("%s = %s", self.name, data)
            self.data.append(data)
        else:
            _LOGGER.info("Did not receive any data from Mi Flora sensor %s",
                         self.name)
            # Remove old data from median list or set sensor value to None
            # if no data is available anymore
            if len(self.data) > 0:
                self.data = self.data[1:]
            else:
                self._state = None
            return

        _LOGGER.debug("Data collected: %s", self.data)
        if len(self.data) > self.median_count:
            self.data = self.data[1:]

        if len(self.data) == self.median_count:
            median = sorted(self.data)[int((self.median_count - 1) / 2)]
            _LOGGER.debug("Median is: %s", median)
            self._state = median
        else:
            _LOGGER.debug("Not yet enough data for median calculation")

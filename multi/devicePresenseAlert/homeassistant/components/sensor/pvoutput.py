"""
Support for getting collected information from PVOutput.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.pvoutput/
"""
import logging
from collections import namedtuple

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.components.sensor.rest import RestData
from homeassistant.const import (
    ATTR_TEMPERATURE, CONF_API_KEY, CONF_NAME, STATE_UNKNOWN)

_LOGGER = logging.getLogger(__name__)
_ENDPOINT = 'http://pvoutput.org/service/r2/getstatus.jsp'

ATTR_DATE = 'date'
ATTR_TIME = 'time'
ATTR_ENERGY_GENERATION = 'energy_generation'
ATTR_POWER_GENERATION = 'power_generation'
ATTR_ENERGY_CONSUMPTION = 'energy_consumption'
ATTR_POWER_CONSUMPTION = 'power_consumption'
ATTR_EFFICIENCY = 'efficiency'
ATTR_VOLTAGE = 'voltage'

CONF_SYSTEM_ID = 'system_id'

DEFAULT_NAME = 'PVOutput'
DEFAULT_VERIFY_SSL = True

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_SYSTEM_ID): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the PVOutput sensor."""
    name = config.get(CONF_NAME)
    api_key = config.get(CONF_API_KEY)
    system_id = config.get(CONF_SYSTEM_ID)
    method = 'GET'
    payload = auth = None
    verify_ssl = DEFAULT_VERIFY_SSL
    headers = {
        'X-Pvoutput-Apikey': api_key,
        'X-Pvoutput-SystemId': system_id,
    }

    rest = RestData(method, _ENDPOINT, auth, headers, payload, verify_ssl)
    rest.update()

    if rest.data is None:
        _LOGGER.error("Unable to fetch data from PVOutput")
        return False

    add_devices([PvoutputSensor(rest, name)])


# pylint: disable=no-member
class PvoutputSensor(Entity):
    """Representation of a PVOutput sensor."""

    def __init__(self, rest, name):
        """Initialize a PVOutput sensor."""
        self.rest = rest
        self._name = name
        self.pvcoutput = False
        self.status = namedtuple(
            'status', [ATTR_DATE, ATTR_TIME, ATTR_ENERGY_GENERATION,
                       ATTR_POWER_GENERATION, ATTR_ENERGY_CONSUMPTION,
                       ATTR_POWER_CONSUMPTION, ATTR_EFFICIENCY,
                       ATTR_TEMPERATURE, ATTR_VOLTAGE])

        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        if self.pvcoutput is not None:
            return self.pvcoutput.energy_generation
        else:
            return STATE_UNKNOWN

    @property
    def device_state_attributes(self):
        """Return the state attributes of the monitored installation."""
        if self.pvcoutput is not None:
            return {
                ATTR_ENERGY_GENERATION: self.pvcoutput.energy_generation,
                ATTR_POWER_GENERATION: self.pvcoutput.power_generation,
                ATTR_ENERGY_CONSUMPTION: self.pvcoutput.energy_consumption,
                ATTR_POWER_CONSUMPTION: self.pvcoutput.power_consumption,
                ATTR_EFFICIENCY: self.pvcoutput.efficiency,
                ATTR_TEMPERATURE: self.pvcoutput.temperature,
                ATTR_VOLTAGE: self.pvcoutput.voltage,
            }

    def update(self):
        """Get the latest data from the PVOutput API and updates the state."""
        try:
            self.rest.update()
            self.pvcoutput = self.status._make(self.rest.data.split(','))
        except TypeError:
            self.pvcoutput = None
            _LOGGER.error(
                "Unable to fetch data from PVOutput. %s", self.rest.data)

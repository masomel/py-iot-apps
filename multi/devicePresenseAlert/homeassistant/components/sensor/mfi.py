"""
Support for Ubiquiti mFi sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.mfi/
"""
import logging

import requests
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_PASSWORD, CONF_USERNAME, TEMP_CELSIUS, STATE_ON, STATE_OFF, CONF_HOST,
    CONF_SSL, CONF_VERIFY_SSL, CONF_PORT)
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['mficlient==0.3.0']

_LOGGER = logging.getLogger(__name__)

DEFAULT_SSL = True
DEFAULT_VERIFY_SSL = True

DIGITS = {
    'volts': 1,
    'amps': 1,
    'active_power': 0,
    'temperature': 1,
}

SENSOR_MODELS = [
    'Ubiquiti mFi-THS',
    'Ubiquiti mFi-CS',
    'Outlet',
    'Input Analog',
    'Input Digital',
]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_PORT): cv.port,
    vol.Optional(CONF_SSL, default=DEFAULT_SSL): cv.boolean,
    vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): cv.boolean,
})


# pylint: disable=unused-variable
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup mFi sensors."""
    host = config.get(CONF_HOST)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    use_tls = config.get(CONF_SSL)
    verify_tls = config.get(CONF_VERIFY_SSL)
    default_port = use_tls and 6443 or 6080
    port = int(config.get(CONF_PORT, default_port))

    from mficlient.client import FailedToLogin, MFiClient

    try:
        client = MFiClient(host, username, password, port=port,
                           use_tls=use_tls, verify=verify_tls)
    except (FailedToLogin, requests.exceptions.ConnectionError) as ex:
        _LOGGER.error('Unable to connect to mFi: %s', str(ex))
        return False

    add_devices(MfiSensor(port, hass)
                for device in client.get_devices()
                for port in device.ports.values()
                if port.model in SENSOR_MODELS)


class MfiSensor(Entity):
    """Representation of a mFi sensor."""

    def __init__(self, port, hass):
        """Initialize the sensor."""
        self._port = port
        self._hass = hass

    @property
    def name(self):
        """Return the name of th sensor."""
        return self._port.label

    @property
    def state(self):
        """Return the state of the sensor."""
        try:
            tag = self._port.tag
        except ValueError:
            tag = None
        if tag is None:
            return STATE_OFF
        elif self._port.model == 'Input Digital':
            return self._port.value > 0 and STATE_ON or STATE_OFF
        else:
            digits = DIGITS.get(self._port.tag, 0)
            return round(self._port.value, digits)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        try:
            tag = self._port.tag
        except ValueError:
            return 'State'

        if tag == 'temperature':
            return TEMP_CELSIUS
        elif tag == 'active_pwr':
            return 'Watts'
        elif self._port.model == 'Input Digital':
            return 'State'
        return tag

    def update(self):
        """Get the latest data."""
        self._port.refresh()

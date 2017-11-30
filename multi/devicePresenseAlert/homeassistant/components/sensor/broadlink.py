
"""
Support for the Broadlink RM2 Pro (only temperature) and A1 devices.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.broadlink/
"""
from datetime import timedelta
import binascii
import logging
import socket
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_HOST, CONF_MAC,
                                 CONF_MONITORED_CONDITIONS,
                                 CONF_NAME, TEMP_CELSIUS, CONF_TIMEOUT)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['broadlink==0.3']

_LOGGER = logging.getLogger(__name__)

CONF_UPDATE_INTERVAL = 'update_interval'
DEVICE_DEFAULT_NAME = 'Broadlink sensor'
DEFAULT_TIMEOUT = 10

SENSOR_TYPES = {
    'temperature': ['Temperature', TEMP_CELSIUS],
    'air_quality': ['Air Quality', ' '],
    'humidity': ['Humidity', '%'],
    'light': ['Light', ' '],
    'noise': ['Noise', ' ']
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEVICE_DEFAULT_NAME): vol.Coerce(str),
    vol.Optional(CONF_MONITORED_CONDITIONS, default=[]):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
    vol.Optional(CONF_UPDATE_INTERVAL, default=timedelta(seconds=300)): (
        vol.All(cv.time_period, cv.positive_timedelta)),
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_MAC): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int
})


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Broadlink device sensors."""
    mac = config.get(CONF_MAC).encode().replace(b':', b'')
    mac_addr = binascii.unhexlify(mac)
    broadlink_data = BroadlinkData(
        config.get(CONF_UPDATE_INTERVAL),
        config.get(CONF_HOST),
        mac_addr, config.get(CONF_TIMEOUT))

    dev = []
    for variable in config[CONF_MONITORED_CONDITIONS]:
        dev.append(BroadlinkSensor(
            config.get(CONF_NAME),
            broadlink_data,
            variable))
    add_devices(dev)


class BroadlinkSensor(Entity):
    """Representation of a Broadlink device sensor."""

    def __init__(self, name, broadlink_data, sensor_type):
        """Initialize the sensor."""
        self._name = "%s %s" % (name, SENSOR_TYPES[sensor_type][0])
        self._state = None
        self._type = sensor_type
        self._broadlink_data = broadlink_data
        self._unit_of_measurement = SENSOR_TYPES[sensor_type][1]
        self.update()

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
        """Return the unit this state is expressed in."""
        return self._unit_of_measurement

    def update(self):
        """Get the latest data from the sensor."""
        self._broadlink_data.update()
        if self._broadlink_data.data is None:
            return
        self._state = self._broadlink_data.data[self._type]


class BroadlinkData(object):
    """Representation of a Broadlink data object."""

    def __init__(self, interval, ip_addr, mac_addr, timeout):
        """Initialize the data object."""
        import broadlink
        self.data = None
        self._device = broadlink.a1((ip_addr, 80), mac_addr)
        self._device.timeout = timeout
        self.update = Throttle(interval)(self._update)
        if not self._auth():
            _LOGGER.error("Failed to connect to device.")

    def _update(self, retry=2):
        try:
            self.data = self._device.check_sensors_raw()
        except socket.timeout as error:
            if retry < 1:
                _LOGGER.error(error)
                return
            if not self._auth():
                return
            return self._update(max(0, retry-1))

    def _auth(self, retry=2):
        try:
            auth = self._device.auth()
        except socket.timeout:
            auth = False
        if not auth and retry > 0:
            return self._auth(max(0, retry-1))
        return auth

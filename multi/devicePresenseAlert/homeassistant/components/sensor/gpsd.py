"""
Support for GPSD.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.gpsd/
"""
import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_LATITUDE, ATTR_LONGITUDE, STATE_UNKNOWN, CONF_HOST, CONF_PORT,
    CONF_NAME)
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['gps3==0.33.3']

_LOGGER = logging.getLogger(__name__)

ATTR_CLIMB = 'climb'
ATTR_ELEVATION = 'elevation'
ATTR_GPS_TIME = 'gps_time'
ATTR_MODE = 'mode'
ATTR_SPEED = 'speed'

DEFAULT_HOST = 'localhost'
DEFAULT_NAME = 'GPS'
DEFAULT_PORT = 2947

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the GPSD component."""
    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)

    # Will hopefully be possible with the next gps3 update
    # https://github.com/wadda/gps3/issues/11
    # from gps3 import gps3
    # try:
    #     gpsd_socket = gps3.GPSDSocket()
    #     gpsd_socket.connect(host=host, port=port)
    # except GPSError:
    #     _LOGGER.warning('Not able to connect to GPSD')
    #     return False
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
        sock.shutdown(2)
        _LOGGER.debug('Connection to GPSD possible')
    except socket.error:
        _LOGGER.error('Not able to connect to GPSD')
        return False

    add_devices([GpsdSensor(hass, name, host, port)])


class GpsdSensor(Entity):
    """Representation of a GPS receiver available via GPSD."""

    def __init__(self, hass, name, host, port):
        """Initialize the GPSD sensor."""
        from gps3.agps3threaded import AGPS3mechanism

        self.hass = hass
        self._name = name
        self._host = host
        self._port = port

        self.agps_thread = AGPS3mechanism()
        self.agps_thread.stream_data(host=self._host, port=self._port)
        self.agps_thread.run_thread()

    @property
    def name(self):
        """Return the name."""
        return self._name

    # pylint: disable=no-member
    @property
    def state(self):
        """Return the state of GPSD."""
        if self.agps_thread.data_stream.mode == 3:
            return "3D Fix"
        elif self.agps_thread.data_stream.mode == 2:
            return "2D Fix"
        else:
            return STATE_UNKNOWN

    @property
    def state_attributes(self):
        """Return the state attributes of the GPS."""
        return {
            ATTR_LATITUDE: self.agps_thread.data_stream.lat,
            ATTR_LONGITUDE: self.agps_thread.data_stream.lon,
            ATTR_ELEVATION: self.agps_thread.data_stream.alt,
            ATTR_GPS_TIME: self.agps_thread.data_stream.time,
            ATTR_SPEED: self.agps_thread.data_stream.speed,
            ATTR_CLIMB: self.agps_thread.data_stream.climb,
            ATTR_MODE: self.agps_thread.data_stream.mode,
        }

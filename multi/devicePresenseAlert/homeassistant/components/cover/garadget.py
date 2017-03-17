"""
Platform for the garadget cover component.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/garadget/
"""
import logging

import voluptuous as vol

import requests

from homeassistant.components.cover import CoverDevice, PLATFORM_SCHEMA
from homeassistant.helpers.event import track_utc_time_change
from homeassistant.const import CONF_DEVICE, CONF_USERNAME, CONF_PASSWORD,\
    CONF_ACCESS_TOKEN, CONF_NAME, STATE_UNKNOWN, STATE_CLOSED, STATE_OPEN,\
    CONF_COVERS
import homeassistant.helpers.config_validation as cv

DEFAULT_NAME = 'Garadget'

ATTR_SIGNAL_STRENGTH = "wifi signal strength (dB)"
ATTR_TIME_IN_STATE = "time in state"
ATTR_SENSOR_STRENGTH = "sensor reflection rate"
ATTR_AVAILABLE = "available"

STATE_OPENING = "opening"
STATE_CLOSING = "closing"
STATE_STOPPED = "stopped"
STATE_OFFLINE = "offline"

STATES_MAP = {
    "open": STATE_OPEN,
    "opening": STATE_OPENING,
    "closed": STATE_CLOSED,
    "closing": STATE_CLOSING,
    "stopped": STATE_STOPPED
}


# Validation of the user's configuration
COVER_SCHEMA = vol.Schema({
    vol.Optional(CONF_DEVICE): cv.string,
    vol.Optional(CONF_USERNAME): cv.string,
    vol.Optional(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_ACCESS_TOKEN): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_COVERS): vol.Schema({cv.slug: COVER_SCHEMA}),
})

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Demo covers."""
    covers = []
    devices = config.get(CONF_COVERS, {})

    _LOGGER.debug(devices)

    for device_id, device_config in devices.items():
        args = {
            "name": device_config.get(CONF_NAME),
            "device_id": device_config.get(CONF_DEVICE, device_id),
            "username": device_config.get(CONF_USERNAME),
            "password": device_config.get(CONF_PASSWORD),
            "access_token": device_config.get(CONF_ACCESS_TOKEN)
        }

        covers.append(GaradgetCover(hass, args))

    add_devices(covers)


class GaradgetCover(CoverDevice):
    """Representation of a demo cover."""

    # pylint: disable=no-self-use, too-many-instance-attributes
    def __init__(self, hass, args):
        """Initialize the cover."""
        self.particle_url = 'https://api.particle.io'
        self.hass = hass
        self._name = args['name']
        self.device_id = args['device_id']
        self.access_token = args['access_token']
        self.obtained_token = False
        self._username = args['username']
        self._password = args['password']
        self._state = STATE_UNKNOWN
        self.time_in_state = None
        self.signal = None
        self.sensor = None
        self._unsub_listener_cover = None
        self._available = True

        if self.access_token is None:
            self.access_token = self.get_token()
            self._obtained_token = True

        # Lets try to get the configured name if not provided.
        try:
            if self._name is None:
                doorconfig = self._get_variable("doorConfig")
                if doorconfig["nme"] is not None:
                    self._name = doorconfig["nme"]
            self.update()
        except requests.exceptions.ConnectionError as ex:
            _LOGGER.error('Unable to connect to server: %(reason)s',
                          dict(reason=ex))
            self._state = STATE_OFFLINE
            self._available = False
            self._name = DEFAULT_NAME
        except KeyError as ex:
            _LOGGER.warning('Garadget device %(device)s seems to be offline',
                            dict(device=self.device_id))
            self._name = DEFAULT_NAME
            self._state = STATE_OFFLINE
            self._available = False

    def __del__(self):
        """Try to remove token."""
        if self._obtained_token is True:
            if self.access_token is not None:
                self.remove_token()

    @property
    def name(self):
        """Return the name of the cover."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed for a demo cover."""
        return True

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        data = {}

        if self.signal is not None:
            data[ATTR_SIGNAL_STRENGTH] = self.signal

        if self.time_in_state is not None:
            data[ATTR_TIME_IN_STATE] = self.time_in_state

        if self.sensor is not None:
            data[ATTR_SENSOR_STRENGTH] = self.sensor

        if self.access_token is not None:
            data[CONF_ACCESS_TOKEN] = self.access_token

        return data

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        if self._state == STATE_UNKNOWN:
            return None
        else:
            return self._state == STATE_CLOSED

    def get_token(self):
        """Get new token for usage during this session."""
        args = {
            'grant_type': 'password',
            'username': self._username,
            'password': self._password
        }
        url = '{}/oauth/token'.format(self.particle_url)
        ret = requests.post(url,
                            auth=('particle', 'particle'),
                            data=args)

        return ret.json()['access_token']

    def remove_token(self):
        """Remove authorization token from API."""
        ret = requests.delete('{}/v1/access_tokens/{}'.format(
            self.particle_url,
            self.access_token),
                              auth=(self._username, self._password))
        return ret.text

    def _start_watcher(self, command):
        """Start watcher."""
        _LOGGER.debug("Starting Watcher for command: %s ", command)
        if self._unsub_listener_cover is None:
            self._unsub_listener_cover = track_utc_time_change(
                self.hass, self._check_state)

    def _check_state(self, now):
        """Check the state of the service during an operation."""
        self.update()
        self.update_ha_state()

    def close_cover(self):
        """Close the cover."""
        if self._state not in ["close", "closing"]:
            ret = self._put_command("setState", "close")
            self._start_watcher('close')
            return ret.get('return_value') == 1

    def open_cover(self):
        """Open the cover."""
        if self._state not in ["open", "opening"]:
            ret = self._put_command("setState", "open")
            self._start_watcher('open')
            return ret.get('return_value') == 1

    def stop_cover(self):
        """Stop the door where it is."""
        if self._state not in ["stopped"]:
            ret = self._put_command("setState", "stop")
            self._start_watcher('stop')
            return ret['return_value'] == 1

    def update(self):
        """Get updated status from API."""
        try:
            status = self._get_variable("doorStatus")
            _LOGGER.debug("Current Status: %s", status['status'])
            self._state = STATES_MAP.get(status['status'], STATE_UNKNOWN)
            self.time_in_state = status['time']
            self.signal = status['signal']
            self.sensor = status['sensor']
            self._availble = True
        except requests.exceptions.ConnectionError as ex:
            _LOGGER.error('Unable to connect to server: %(reason)s',
                          dict(reason=ex))
            self._state = STATE_OFFLINE
        except KeyError as ex:
            _LOGGER.warning('Garadget device %(device)s seems to be offline',
                            dict(device=self.device_id))
            self._state = STATE_OFFLINE

        if self._state not in [STATE_CLOSING, STATE_OPENING]:
            if self._unsub_listener_cover is not None:
                self._unsub_listener_cover()
                self._unsub_listener_cover = None

    def _get_variable(self, var):
        """Get latest status."""
        url = '{}/v1/devices/{}/{}?access_token={}'.format(
            self.particle_url,
            self.device_id,
            var,
            self.access_token,
            )
        ret = requests.get(url)
        result = {}
        for pairs in ret.json()['result'].split('|'):
            key = pairs.split('=')
            result[key[0]] = key[1]
        return result

    def _put_command(self, func, arg=None):
        """Send commands to API."""
        params = {'access_token': self.access_token}
        if arg:
            params['command'] = arg
        url = '{}/v1/devices/{}/{}'.format(
            self.particle_url,
            self.device_id,
            func)
        ret = requests.post(url, data=params)
        return ret.json()

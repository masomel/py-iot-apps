"""
Interfaces with Alarm.com alarm control panels.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/alarm_control_panel.alarmdotcom/
"""
import logging

import voluptuous as vol

import homeassistant.components.alarm_control_panel as alarm
from homeassistant.components.alarm_control_panel import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_PASSWORD, CONF_USERNAME, STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME, STATE_ALARM_DISARMED, STATE_UNKNOWN, CONF_CODE,
    CONF_NAME)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['https://github.com/Xorso/pyalarmdotcom'
                '/archive/0.1.1.zip'
                '#pyalarmdotcom==0.1.1']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Alarm.com'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Optional(CONF_CODE): cv.positive_int,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup an Alarm.com control panel."""
    name = config.get(CONF_NAME)
    code = config.get(CONF_CODE)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    add_devices([AlarmDotCom(hass, name, code, username, password)], True)


class AlarmDotCom(alarm.AlarmControlPanel):
    """Represent an Alarm.com status."""

    def __init__(self, hass, name, code, username, password):
        """Initialize the Alarm.com status."""
        from pyalarmdotcom.pyalarmdotcom import Alarmdotcom
        self._alarm = Alarmdotcom(username, password, timeout=10)
        self._hass = hass
        self._name = name
        self._code = str(code) if code else None
        self._username = username
        self._password = password
        self._state = STATE_UNKNOWN

    def update(self):
        """Fetch the latest state."""
        self._state = self._alarm.state

    @property
    def name(self):
        """Return the name of the alarm."""
        return self._name

    @property
    def code_format(self):
        """One or more characters if code is defined."""
        return None if self._code is None else '.+'

    @property
    def state(self):
        """Return the state of the device."""
        if self._state == 'Disarmed':
            return STATE_ALARM_DISARMED
        elif self._state == 'Armed Stay':
            return STATE_ALARM_ARMED_HOME
        elif self._state == 'Armed Away':
            return STATE_ALARM_ARMED_AWAY
        else:
            return STATE_UNKNOWN

    def alarm_disarm(self, code=None):
        """Send disarm command."""
        if not self._validate_code(code, 'disarming home'):
            return
        from pyalarmdotcom.pyalarmdotcom import Alarmdotcom
        # Open another session to alarm.com to fire off the command
        _alarm = Alarmdotcom(self._username, self._password, timeout=10)
        _alarm.disarm()

    def alarm_arm_home(self, code=None):
        """Send arm home command."""
        if not self._validate_code(code, 'arming home'):
            return
        from pyalarmdotcom.pyalarmdotcom import Alarmdotcom
        # Open another session to alarm.com to fire off the command
        _alarm = Alarmdotcom(self._username, self._password, timeout=10)
        _alarm.arm_stay()

    def alarm_arm_away(self, code=None):
        """Send arm away command."""
        if not self._validate_code(code, 'arming home'):
            return
        from pyalarmdotcom.pyalarmdotcom import Alarmdotcom
        # Open another session to alarm.com to fire off the command
        _alarm = Alarmdotcom(self._username, self._password, timeout=10)
        _alarm.arm_away()

    def _validate_code(self, code, state):
        """Validate given code."""
        check = self._code is None or code == self._code
        if not check:
            _LOGGER.warning('Wrong code entered for %s', state)
        return check

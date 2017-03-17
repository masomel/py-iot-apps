"""
Support for Neato Connected Vaccums switches.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.neato/
"""
import logging

from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.components.neato import NEATO_ROBOTS, NEATO_LOGIN

_LOGGER = logging.getLogger(__name__)

SWITCH_TYPE_CLEAN = 'clean'
SWITCH_TYPE_SCHEDULE = 'scedule'

SWITCH_TYPES = {
    SWITCH_TYPE_CLEAN: ['Clean'],
    SWITCH_TYPE_SCHEDULE: ['Schedule']
}


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Neato switches."""
    if not hass.data[NEATO_ROBOTS]:
        return False

    dev = []
    for robot in hass.data[NEATO_ROBOTS]:
        for type_name in SWITCH_TYPES:
            dev.append(NeatoConnectedSwitch(hass, robot, type_name))
    _LOGGER.debug('Adding switches %s', dev)
    add_devices(dev)


class NeatoConnectedSwitch(ToggleEntity):
    """Neato Connected Switches."""

    def __init__(self, hass, robot, switch_type):
        """Initialize the Neato Connected switches."""
        self.type = switch_type
        self.robot = robot
        self.neato = hass.data[NEATO_LOGIN]
        self._robot_name = self.robot.name + ' ' + SWITCH_TYPES[self.type][0]
        self._state = self.robot.state
        self._schedule_state = None
        self._clean_state = None

    def update(self):
        """Update the states of Neato switches."""
        _LOGGER.debug('Running switch update')
        self.neato.update_robots()
        if not self._state:
            return
        self._state = self.robot.state
        _LOGGER.debug('self._state=%s', self._state)
        if self.type == SWITCH_TYPE_CLEAN:
            if (self.robot.state['action'] == 1 or
                    self.robot.state['action'] == 2 or
                    self.robot.state['action'] == 3 and
                    self.robot.state['state'] == 2):
                self._clean_state = STATE_ON
            else:
                self._clean_state = STATE_OFF
            _LOGGER.debug('schedule_state=%s', self._schedule_state)
        if self.type == SWITCH_TYPE_SCHEDULE:
            _LOGGER.debug('self._state=%s', self._state)
            if self.robot.schedule_enabled:
                self._schedule_state = STATE_ON
            else:
                self._schedule_state = STATE_OFF
            _LOGGER.debug('schedule_state=%s', self._schedule_state)

    @property
    def name(self):
        """Return the name of the switch."""
        return self._robot_name

    @property
    def available(self):
        """Return True if entity is available."""
        if not self._state:
            return False
        else:
            return True

    @property
    def is_on(self):
        """Return true if switch is on."""
        if self.type == SWITCH_TYPE_CLEAN:
            if self._clean_state == STATE_ON:
                return True
            return False
        elif self.type == SWITCH_TYPE_SCHEDULE:
            if self._schedule_state == STATE_ON:
                return True
            return False

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        if self.type == SWITCH_TYPE_CLEAN:
            self.robot.start_cleaning()
        elif self.type == SWITCH_TYPE_SCHEDULE:
            self.robot.enable_schedule()

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        if self.type == SWITCH_TYPE_CLEAN:
            self.robot.pause_cleaning()
            self.robot.send_to_base()
        elif self.type == SWITCH_TYPE_SCHEDULE:
            self.robot.disable_schedule()

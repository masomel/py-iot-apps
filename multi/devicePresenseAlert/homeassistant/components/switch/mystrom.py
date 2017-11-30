"""
Support for myStrom switches.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/switch.mystrom/
"""
import logging

import voluptuous as vol

from homeassistant.components.switch import (SwitchDevice, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_NAME, CONF_HOST)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['python-mystrom==0.3.6']

DEFAULT_NAME = 'myStrom Switch'

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Find and return myStrom switch."""
    from pymystrom import MyStromPlug, exceptions

    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)

    try:
        MyStromPlug(host).get_status()
    except exceptions.MyStromConnectionError:
        _LOGGER.error("No route to device '%s'", host)
        return False

    add_devices([MyStromSwitch(name, host)])


class MyStromSwitch(SwitchDevice):
    """Representation of a myStrom switch."""

    def __init__(self, name, resource):
        """Initialize the myStrom switch."""
        from pymystrom import MyStromPlug

        self._name = name
        self._resource = resource
        self.data = {}
        self.plug = MyStromPlug(self._resource)
        self.update()

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self):
        """Return true if switch is on."""
        return bool(self.data['relay'])

    @property
    def current_power_mwh(self):
        """Return the current power consumption in mWh."""
        return round(self.data['power'], 2)

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        from pymystrom import exceptions
        try:
            self.plug.set_relay_on()
        except exceptions.MyStromConnectionError:
            _LOGGER.error("No route to device '%s'. Is device offline?",
                          self._resource)

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        from pymystrom import exceptions
        try:
            self.plug.set_relay_off()
        except exceptions.MyStromConnectionError:
            _LOGGER.error("No route to device '%s'. Is device offline?",
                          self._resource)

    def update(self):
        """Get the latest data from the device and update the data."""
        from pymystrom import exceptions
        try:
            self.data = self.plug.get_status()
        except exceptions.MyStromConnectionError:
            self.data = {'power': 0, 'relay': False}
            _LOGGER.error("No route to device '%s'. Is device offline?",
                          self._resource)

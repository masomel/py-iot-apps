"""
Allows to configure a switch using BBB GPIO.

Switch example for two GPIOs pins P9_12 and P9_42
Allowed GPIO pin name is GPIOxxx or Px_x

switch:
  - platform: bbb_gpio
    pins:
      GPIO0_7:
        name: LED Red
      P9_12:
        name: LED Green
        initial: true
        invert_logic: true
"""
import logging

import voluptuous as vol

from homeassistant.components.switch import PLATFORM_SCHEMA
import homeassistant.components.bbb_gpio as bbb_gpio
from homeassistant.const import (DEVICE_DEFAULT_NAME, CONF_NAME)
from homeassistant.helpers.entity import ToggleEntity
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['bbb_gpio']

CONF_PINS = 'pins'
CONF_INITIAL = 'initial'
CONF_INVERT_LOGIC = 'invert_logic'

PIN_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_INITIAL, default=False): cv.boolean,
    vol.Optional(CONF_INVERT_LOGIC, default=False): cv.boolean,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PINS, default={}):
        vol.Schema({cv.string: PIN_SCHEMA}),
})


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Beaglebone GPIO devices."""
    pins = config.get(CONF_PINS)

    switches = []
    for pin, params in list(pins.items()):
        switches.append(BBBGPIOSwitch(pin, params))
    add_devices(switches)


class BBBGPIOSwitch(ToggleEntity):
    """Representation of a  Beaglebone GPIO."""

    def __init__(self, pin, params):
        """Initialize the pin."""
        self._pin = pin
        self._name = params.get(CONF_NAME) or DEVICE_DEFAULT_NAME
        self._state = params.get(CONF_INITIAL)
        self._invert_logic = params.get(CONF_INVERT_LOGIC)

        bbb_gpio.setup_output(self._pin)

        if self._state is False:
            bbb_gpio.write_output(self._pin, 1 if self._invert_logic else 0)
        else:
            bbb_gpio.write_output(self._pin, 0 if self._invert_logic else 1)

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    def turn_on(self):
        """Turn the device on."""
        bbb_gpio.write_output(self._pin, 0 if self._invert_logic else 1)
        self._state = True
        self.schedule_update_ha_state()

    def turn_off(self):
        """Turn the device off."""
        bbb_gpio.write_output(self._pin, 1 if self._invert_logic else 0)
        self._state = False
        self.schedule_update_ha_state()

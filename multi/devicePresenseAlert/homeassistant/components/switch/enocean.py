"""
Support for EnOcean switches.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.enocean/
"""
import logging

import voluptuous as vol

from homeassistant.components.switch import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_ID)
from homeassistant.components import enocean
from homeassistant.helpers.entity import ToggleEntity
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'EnOcean Switch'
DEPENDENCIES = ['enocean']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ID): vol.All(cv.ensure_list, [vol.Coerce(int)]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the EnOcean switch platform."""
    dev_id = config.get(CONF_ID)
    devname = config.get(CONF_NAME)

    add_devices([EnOceanSwitch(dev_id, devname)])


class EnOceanSwitch(enocean.EnOceanDevice, ToggleEntity):
    """Representation of an EnOcean switch device."""

    def __init__(self, dev_id, devname):
        """Initialize the EnOcean switch device."""
        enocean.EnOceanDevice.__init__(self)
        self.dev_id = dev_id
        self._devname = devname
        self._light = None
        self._on_state = False
        self._on_state2 = False
        self.stype = "switch"

    @property
    def is_on(self):
        """Return whether the switch is on or off."""
        return self._on_state

    @property
    def name(self):
        """Return the device name."""
        return self._devname

    def turn_on(self, **kwargs):
        """Turn on the switch."""
        optional = [0x03, ]
        optional.extend(self.dev_id)
        optional.extend([0xff, 0x00])
        self.send_command(data=[0xD2, 0x01, 0x00, 0x64, 0x00,
                                0x00, 0x00, 0x00, 0x00], optional=optional,
                          packet_type=0x01)
        self._on_state = True

    def turn_off(self, **kwargs):
        """Turn off the switch."""
        optional = [0x03, ]
        optional.extend(self.dev_id)
        optional.extend([0xff, 0x00])
        self.send_command(data=[0xD2, 0x01, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00], optional=optional,
                          packet_type=0x01)
        self._on_state = False

    def value_changed(self, val):
        """Update the internal state of the switch."""
        self._on_state = val
        self.schedule_update_ha_state()

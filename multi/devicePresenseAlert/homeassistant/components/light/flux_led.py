"""
Support for Flux lights.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.flux_led/
"""
import logging
import socket
import random

import voluptuous as vol

from homeassistant.const import CONF_DEVICES, CONF_NAME, CONF_PROTOCOL
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_RGB_COLOR, ATTR_EFFECT, EFFECT_RANDOM,
    SUPPORT_BRIGHTNESS, SUPPORT_EFFECT, SUPPORT_RGB_COLOR, Light,
    PLATFORM_SCHEMA)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['flux_led==0.12']

_LOGGER = logging.getLogger(__name__)

CONF_AUTOMATIC_ADD = 'automatic_add'
ATTR_MODE = 'mode'

DOMAIN = 'flux_led'

SUPPORT_FLUX_LED = (SUPPORT_BRIGHTNESS | SUPPORT_EFFECT |
                    SUPPORT_RGB_COLOR)

DEVICE_SCHEMA = vol.Schema({
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(ATTR_MODE, default='rgbw'):
        vol.All(cv.string, vol.In(['rgbw', 'rgb'])),
    vol.Optional(CONF_PROTOCOL, default=None):
        vol.All(cv.string, vol.In(['ledenet'])),
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_DEVICES, default={}): {cv.string: DEVICE_SCHEMA},
    vol.Optional(CONF_AUTOMATIC_ADD, default=False):  cv.boolean,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Flux lights."""
    from . import flux_led
    lights = []
    light_ips = []
    for ipaddr, device_config in list(config[CONF_DEVICES].items()):
        device = {}
        device['name'] = device_config[CONF_NAME]
        device['ipaddr'] = ipaddr
        device[CONF_PROTOCOL] = device_config[CONF_PROTOCOL]
        device[ATTR_MODE] = device_config[ATTR_MODE]
        light = FluxLight(device)
        if light.is_valid:
            lights.append(light)
            light_ips.append(ipaddr)

    if not config[CONF_AUTOMATIC_ADD]:
        add_devices(lights)
        return

    # Find the bulbs on the LAN
    scanner = flux_led.BulbScanner()
    scanner.scan(timeout=10)
    for device in scanner.getBulbInfo():
        ipaddr = device['ipaddr']
        if ipaddr in light_ips:
            continue
        device['name'] = device['id'] + " " + ipaddr
        device[ATTR_MODE] = 'rgbw'
        light = FluxLight(device)
        if light.is_valid:
            lights.append(light)
            light_ips.append(ipaddr)

    add_devices(lights)


class FluxLight(Light):
    """Representation of a Flux light."""

    def __init__(self, device):
        """Initialize the light."""
        from . import flux_led

        self._name = device['name']
        self._ipaddr = device['ipaddr']
        self._protocol = device[CONF_PROTOCOL]
        self._mode = device[ATTR_MODE]
        self.is_valid = True
        self._bulb = None
        try:
            self._bulb = flux_led.WifiLedBulb(self._ipaddr)
            if self._protocol:
                self._bulb.setProtocol(self._protocol)
        except socket.error:
            self.is_valid = False
            _LOGGER.error(
                "Failed to connect to bulb %s, %s", self._ipaddr, self._name)

    @property
    def unique_id(self):
        """Return the ID of this light."""
        return "{}.{}".format(self.__class__, self._ipaddr)

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._bulb.isOn()

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        return self._bulb.getWarmWhite255()

    @property
    def rgb_color(self):
        """Return the color property."""
        return self._bulb.getRgb()

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_FLUX_LED

    def turn_on(self, **kwargs):
        """Turn the specified or all lights on."""
        if not self.is_on:
            self._bulb.turnOn()

        rgb = kwargs.get(ATTR_RGB_COLOR)
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        effect = kwargs.get(ATTR_EFFECT)
        if rgb is not None and brightness is not None:
            self._bulb.setRgb(*tuple(rgb), brightness=brightness)
        elif rgb is not None:
            self._bulb.setRgb(*tuple(rgb))
        elif brightness is not None:
            if self._mode == 'rgbw':
                self._bulb.setWarmWhite255(brightness)
            elif self._mode == 'rgb':
                (red, green, blue) = self._bulb.getRgb()
                self._bulb.setRgb(red, green, blue, brightness=brightness)
        elif effect == EFFECT_RANDOM:
            self._bulb.setRgb(random.randrange(0, 255),
                              random.randrange(0, 255),
                              random.randrange(0, 255))

    def turn_off(self, **kwargs):
        """Turn the specified or all lights off."""
        self._bulb.turnOff()

    def update(self):
        """Synchronize state with bulb."""
        self._bulb.refreshState()

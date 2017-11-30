"""
Support for LiteJet lights.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.litejet/
"""
import logging

import homeassistant.components.litejet as litejet
from homeassistant.components.light import ATTR_BRIGHTNESS, Light

DEPENDENCIES = ['litejet']

ATTR_NUMBER = 'number'

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up lights for the LiteJet platform."""
    litejet_ = hass.data['litejet_system']

    devices = []
    for i in litejet_.loads():
        name = litejet_.get_load_name(i)
        if not litejet.is_ignored(hass, name):
            devices.append(LiteJetLight(hass, litejet_, i, name))
    add_devices(devices)


class LiteJetLight(Light):
    """Representation of a single LiteJet light."""

    def __init__(self, hass, lj, i, name):
        """Initialize a LiteJet light."""
        self._hass = hass
        self._lj = lj
        self._index = i
        self._brightness = 0
        self._name = name

        lj.on_load_activated(i, self._on_load_changed)
        lj.on_load_deactivated(i, self._on_load_changed)

        self.update()

    def _on_load_changed(self):
        """Called on a LiteJet thread when a load's state changes."""
        _LOGGER.debug("Updating due to notification for %s", self._name)
        self._hass.async_add_job(self.async_update_ha_state(True))

    @property
    def name(self):
        """The light's name."""
        return self._name

    @property
    def brightness(self):
        """Return the light's brightness."""
        return self._brightness

    @property
    def is_on(self):
        """Return if the light is on."""
        return self._brightness != 0

    @property
    def should_poll(self):
        """Return that lights do not require polling."""
        return False

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        return {
            ATTR_NUMBER: self._index
        }

    def turn_on(self, **kwargs):
        """Turn on the light."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness = int(kwargs[ATTR_BRIGHTNESS] / 255 * 99)
            self._lj.activate_load_at(self._index, brightness, 0)
        else:
            self._lj.activate_load(self._index)

    def turn_off(self, **kwargs):
        """Turn off the light."""
        self._lj.deactivate_load(self._index)

    def update(self):
        """Retrieve the light's brightness from the LiteJet system."""
        self._brightness = self._lj.get_load_level(self._index) / 99 * 255

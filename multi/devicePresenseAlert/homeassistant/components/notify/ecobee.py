"""
Support for ecobee Send Message service.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/notify.ecobee/
"""
import logging

import voluptuous as vol

from homeassistant.components import ecobee
from homeassistant.components.notify import (
    BaseNotificationService, PLATFORM_SCHEMA)  # NOQA
import homeassistant.helpers.config_validation as cv

DEPENDENCIES = ['ecobee']
_LOGGER = logging.getLogger(__name__)


CONF_INDEX = 'index'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_INDEX, default=0): cv.positive_int,
})


def get_service(hass, config):
    """Get the Ecobee notification service."""
    index = config.get(CONF_INDEX)
    return EcobeeNotificationService(index)


class EcobeeNotificationService(BaseNotificationService):
    """Implement the notification service for the Ecobee thermostat."""

    def __init__(self, thermostat_index):
        """Initialize the service."""
        self.thermostat_index = thermostat_index

    def send_message(self, message="", **kwargs):
        """Send a message to a command line."""
        ecobee.NETWORK.ecobee.send_message(self.thermostat_index, message)

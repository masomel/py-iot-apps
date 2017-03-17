"""
Sensor for Supervisord process status.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.supervisord/
"""
import logging
import xmlrpc.client

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_URL
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_URL = 'http://localhost:9001/RPC2'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_URL, default=DEFAULT_URL): cv.url,
})


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Supervisord platform."""
    url = config.get(CONF_URL)
    try:
        supervisor_server = xmlrpc.client.ServerProxy(url)
    except ConnectionRefusedError:
        _LOGGER.error('Could not connect to Supervisord')
        return False

    processes = supervisor_server.supervisor.getAllProcessInfo()

    add_devices(
        [SupervisorProcessSensor(info, supervisor_server)
         for info in processes])


class SupervisorProcessSensor(Entity):
    """Representation of a supervisor-monitored process."""

    def __init__(self, info, server):
        """Initialize the sensor."""
        self._info = info
        self._server = server
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._info.get('name')

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._info.get('statename')

    def update(self):
        """Update device state."""
        self._info = self._server.supervisor.getProcessInfo(
            self._info.get('name'))

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            'group': self._info.get('group'),
            'description': self._info.get('description')
        }

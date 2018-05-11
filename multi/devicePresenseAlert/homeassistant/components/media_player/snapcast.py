"""
Support for interacting with Snapcast clients.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/media_player.snapcast/
"""
import logging
import socket

import voluptuous as vol

from homeassistant.components.media_player import (
    SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_SET, SUPPORT_SELECT_SOURCE,
    SUPPORT_PLAY, PLATFORM_SCHEMA, MediaPlayerDevice)
from homeassistant.const import (
    STATE_OFF, STATE_IDLE, STATE_PLAYING, STATE_UNKNOWN, CONF_HOST, CONF_PORT)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['snapcast==1.2.2']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'snapcast'

SUPPORT_SNAPCAST = SUPPORT_VOLUME_SET | SUPPORT_VOLUME_MUTE | \
    SUPPORT_SELECT_SOURCE | SUPPORT_PLAY


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT): cv.port,
})


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Snapcast platform."""
    import snapcast.control
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT, snapcast.control.CONTROL_PORT)

    try:
        server = snapcast.control.Snapserver(host, port)
    except socket.gaierror:
        _LOGGER.error('Could not connect to Snapcast server at %s:%d',
                      host, port)
        return False

    add_devices([SnapcastDevice(client) for client in server.clients])


class SnapcastDevice(MediaPlayerDevice):
    """Representation of a Snapcast client device."""

    def __init__(self, client):
        """Initialize the Snapcast device."""
        self._client = client

    @property
    def name(self):
        """Return the name of the device."""
        return self._client.identifier

    @property
    def volume_level(self):
        """Return the volume level."""
        return self._client.volume / 100

    @property
    def is_volume_muted(self):
        """Volume muted."""
        return self._client.muted

    @property
    def supported_media_commands(self):
        """Flag of media commands that are supported."""
        return SUPPORT_SNAPCAST

    @property
    def state(self):
        """Return the state of the player."""
        if not self._client.connected:
            return STATE_OFF
        return {
            'idle': STATE_IDLE,
            'playing': STATE_PLAYING,
            'unknown': STATE_UNKNOWN,
        }.get(self._client.stream.status, STATE_UNKNOWN)

    @property
    def source(self):
        """Return the current input source."""
        return self._client.stream.name

    @property
    def source_list(self):
        """List of available input sources."""
        return list(self._client.streams_by_name().keys())

    def mute_volume(self, mute):
        """Send the mute command."""
        self._client.muted = mute

    def set_volume_level(self, volume):
        """Set the volume level."""
        self._client.volume = round(volume * 100)

    def select_source(self, source):
        """Set input source."""
        streams = self._client.streams_by_name()
        if source in streams:
            self._client.stream = streams[source].identifier

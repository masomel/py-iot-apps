"""
Support for interface with an Aquos TV.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/media_player.aquostv/
"""
import logging

import voluptuous as vol

from homeassistant.components.media_player import (
    SUPPORT_NEXT_TRACK, SUPPORT_PAUSE, SUPPORT_PREVIOUS_TRACK,
    SUPPORT_TURN_ON, SUPPORT_TURN_OFF, SUPPORT_SELECT_SOURCE,
    SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_STEP, SUPPORT_PLAY,
    SUPPORT_VOLUME_SET, MediaPlayerDevice, PLATFORM_SCHEMA)

from homeassistant.const import (
    CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON, STATE_UNKNOWN,
    CONF_PORT, CONF_USERNAME, CONF_PASSWORD, CONF_TIMEOUT)


import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['sharp_aquos_rc==0.3.2']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Sharp Aquos TV'
DEFAULT_PORT = 10002
DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD = 'password'
DEFAULT_TIMEOUT = 0.5
DEFAULT_RETRIES = 2

SUPPORT_SHARPTV = SUPPORT_TURN_OFF | \
    SUPPORT_NEXT_TRACK | SUPPORT_PAUSE | SUPPORT_PREVIOUS_TRACK | \
    SUPPORT_SELECT_SOURCE | SUPPORT_VOLUME_MUTE | SUPPORT_VOLUME_STEP | \
    SUPPORT_VOLUME_SET | SUPPORT_PLAY

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): cv.string,
    vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.string,
    vol.Optional('retries', default=DEFAULT_RETRIES): cv.string,
    vol.Optional('power_on_enabled', default=False): cv.boolean,
})

SOURCES = {0: 'TV / Antenna',
           1: 'HDMI_IN_1',
           2: 'HDMI_IN_2',
           3: 'HDMI_IN_3',
           4: 'HDMI_IN_4',
           5: 'COMPONENT IN',
           6: 'VIDEO_IN_1',
           7: 'VIDEO_IN_2',
           8: 'PC_IN'}


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Sharp Aquos TV platform."""
    import sharp_aquos_rc

    name = config.get(CONF_NAME)
    port = config.get(CONF_PORT)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    power_on_enabled = config.get('power_on_enabled')

    if discovery_info:
        _LOGGER.debug('%s', discovery_info)
        vals = discovery_info.split(':')
        if len(vals) > 1:
            port = vals[1]

        host = vals[0]
        remote = sharp_aquos_rc.TV(host,
                                   port,
                                   username,
                                   password,
                                   timeout=20)
        add_devices([SharpAquosTVDevice(name, remote, power_on_enabled)])
        return True

    host = config.get(CONF_HOST)
    remote = sharp_aquos_rc.TV(host,
                               port,
                               username,
                               password,
                               15,
                               1)

    add_devices([SharpAquosTVDevice(name, remote, power_on_enabled)])
    return True


def _retry(func):
    """Decorator to handle query retries."""
    def wrapper(obj, *args, **kwargs):
        """Wrapper for all query functions."""
        update_retries = 5
        while update_retries > 0:
            try:
                func(obj, *args, **kwargs)
                break
            except (OSError, TypeError, ValueError):
                update_retries -= 1
                if update_retries == 0:
                    obj.set_state(STATE_OFF)
    return wrapper


# pylint: disable=abstract-method
class SharpAquosTVDevice(MediaPlayerDevice):
    """Representation of a Aquos TV."""

    # pylint: disable=too-many-public-methods
    def __init__(self, name, remote, power_on_enabled=False):
        """Initialize the aquos device."""
        global SUPPORT_SHARPTV
        self._power_on_enabled = power_on_enabled
        if self._power_on_enabled:
            SUPPORT_SHARPTV = SUPPORT_SHARPTV | SUPPORT_TURN_ON
        # Save a reference to the imported class
        self._name = name
        # Assume that the TV is not muted
        self._muted = False
        self._state = STATE_UNKNOWN
        self._remote = remote
        self._volume = 0
        self._source = None
        self._source_list = list(SOURCES.values())

    def set_state(self, state):
        """Set TV state."""
        self._state = state

    @_retry
    def update(self):
        """Retrieve the latest data."""
        if self._remote.power() == 1:
            self._state = STATE_ON
        else:
            self._state = STATE_OFF
        # Set TV to be able to remotely power on
        if self._power_on_enabled:
            self._remote.power_on_command_settings(2)
        else:
            self._remote.power_on_command_settings(0)
        # Get mute state
        if self._remote.mute() == 2:
            self._muted = False
        else:
            self._muted = True
        # Get source
        self._source = SOURCES.get(self._remote.input())
        # Get volume
        self._volume = self._remote.volume() / 60

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def source(self):
        """Return the current source."""
        return self._source

    @property
    def source_list(self):
        """Return the source list."""
        return self._source_list

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self._volume

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._muted

    @property
    def supported_media_commands(self):
        """Flag of media commands that are supported."""
        return SUPPORT_SHARPTV

    @_retry
    def turn_off(self):
        """Turn off tvplayer."""
        self._remote.power(0)

    @_retry
    def volume_up(self):
        """Volume up the media player."""
        self._remote.volume(int(self._volume * 60) + 2)

    @_retry
    def volume_down(self):
        """Volume down media player."""
        self._remote.volume(int(self._volume * 60) - 2)

    @_retry
    def set_volume_level(self, level):
        """Set Volume media player."""
        self._remote.volume(int(level * 60))

    @_retry
    def mute_volume(self, mute):
        """Send mute command."""
        self._remote.mute(0)

    @_retry
    def turn_on(self):
        """Turn the media player on."""
        self._remote.power(1)

    @_retry
    def media_play_pause(self):
        """Simulate play pause media player."""
        self._remote.remote_button(40)

    @_retry
    def media_play(self):
        """Send play command."""
        self._remote.remote_button(16)

    @_retry
    def media_pause(self):
        """Send pause command."""
        self._remote.remote_button(16)

    @_retry
    def media_next_track(self):
        """Send next track command."""
        self._remote.remote_button(21)

    @_retry
    def media_previous_track(self):
        """Send the previous track command."""
        self._remote.remote_button(19)

    def select_source(self, source):
        """Set the input source."""
        for key, value in SOURCES.items():
            if source == value:
                self._remote.input(key)

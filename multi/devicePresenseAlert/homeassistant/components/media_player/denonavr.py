"""
Support for Denon AVR receivers using their HTTP interface.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/media_player.denon/
"""

import logging
import voluptuous as vol

from homeassistant.components.media_player import (
    SUPPORT_PAUSE, SUPPORT_NEXT_TRACK, SUPPORT_PREVIOUS_TRACK,
    SUPPORT_TURN_OFF, SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_STEP,
    SUPPORT_SELECT_SOURCE, SUPPORT_PLAY_MEDIA, MEDIA_TYPE_CHANNEL,
    MediaPlayerDevice, PLATFORM_SCHEMA, SUPPORT_TURN_ON,
    MEDIA_TYPE_MUSIC, SUPPORT_VOLUME_SET, SUPPORT_PLAY)
from homeassistant.const import (
    CONF_HOST, STATE_OFF, STATE_PLAYING, STATE_PAUSED,
    CONF_NAME, STATE_ON)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['denonavr==0.3.0']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = None
KEY_DENON_CACHE = 'denonavr_hosts'

SUPPORT_DENON = SUPPORT_VOLUME_STEP | SUPPORT_VOLUME_MUTE | \
    SUPPORT_TURN_ON | SUPPORT_TURN_OFF | \
    SUPPORT_SELECT_SOURCE | SUPPORT_PLAY_MEDIA | \
    SUPPORT_PAUSE | SUPPORT_PREVIOUS_TRACK | \
    SUPPORT_NEXT_TRACK | SUPPORT_VOLUME_SET | SUPPORT_PLAY

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Denon platform."""
    import denonavr

    # Initialize list with receivers to be started
    receivers = []

    cache = hass.data.get(KEY_DENON_CACHE)
    if cache is None:
        cache = hass.data[KEY_DENON_CACHE] = set()

    # Start assignment of host and name
    # 1. option: manual setting
    if config.get(CONF_HOST) is not None:
        host = config.get(CONF_HOST)
        name = config.get(CONF_NAME)
        # Check if host not in cache, append it and save for later starting
        if host not in cache:
            cache.add(host)
            receivers.append(
                DenonDevice(denonavr.DenonAVR(host, name)))
            _LOGGER.info("Denon receiver at host %s initialized", host)
    # 2. option: discovery using netdisco
    if discovery_info is not None:
        host = discovery_info[0]
        name = discovery_info[1]
        # Check if host not in cache, append it and save for later starting
        if host not in cache:
            cache.add(host)
            receivers.append(
                DenonDevice(denonavr.DenonAVR(host, name)))
            _LOGGER.info("Denon receiver at host %s initialized", host)
    # 3. option: discovery using denonavr library
    if config.get(CONF_HOST) is None and discovery_info is None:
        d_receivers = denonavr.discover()
        # More than one receiver could be discovered by that method
        if d_receivers is not None:
            for d_receiver in d_receivers:
                host = d_receiver["host"]
                name = d_receiver["friendlyName"]
                # Check if host not in cache, append it and save for later
                # starting
                if host not in cache:
                    cache.add(host)
                    receivers.append(
                        DenonDevice(denonavr.DenonAVR(host, name)))
                    _LOGGER.info("Denon receiver at host %s initialized", host)

    # Add all freshly discovered receivers
    if receivers:
        add_devices(receivers)


class DenonDevice(MediaPlayerDevice):
    """Representation of a Denon Media Player Device."""

    def __init__(self, receiver):
        """Initialize the device."""
        self._receiver = receiver
        self._name = self._receiver.name
        self._muted = self._receiver.muted
        self._volume = self._receiver.volume
        self._current_source = self._receiver.input_func
        self._source_list = self._receiver.input_func_list
        self._state = self._receiver.state
        self._power = self._receiver.power
        self._media_image_url = self._receiver.image_url
        self._title = self._receiver.title
        self._artist = self._receiver.artist
        self._album = self._receiver.album
        self._band = self._receiver.band
        self._frequency = self._receiver.frequency
        self._station = self._receiver.station

    def update(self):
        """Get the latest status information from device."""
        # Update denonavr
        self._receiver.update()
        # Refresh own data
        self._name = self._receiver.name
        self._muted = self._receiver.muted
        self._volume = self._receiver.volume
        self._current_source = self._receiver.input_func
        self._source_list = self._receiver.input_func_list
        self._state = self._receiver.state
        self._power = self._receiver.power
        self._media_image_url = self._receiver.image_url
        self._title = self._receiver.title
        self._artist = self._receiver.artist
        self._album = self._receiver.album
        self._band = self._receiver.band
        self._frequency = self._receiver.frequency
        self._station = self._receiver.station

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._muted

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        # Volume is sent in a format like -50.0. Minimum is -80.0,
        # maximum is 18.0
        return (float(self._volume) + 80) / 100

    @property
    def source(self):
        """Return the current input source."""
        return self._current_source

    @property
    def source_list(self):
        """List of available input sources."""
        return self._source_list

    @property
    def supported_media_commands(self):
        """Flag of media commands that are supported."""
        return SUPPORT_DENON

    @property
    def media_content_id(self):
        """Content ID of current playing media."""
        return None

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        if self._state == STATE_PLAYING or self._state == STATE_PAUSED:
            return MEDIA_TYPE_MUSIC
        else:
            return MEDIA_TYPE_CHANNEL

    @property
    def media_duration(self):
        """Duration of current playing media in seconds."""
        return None

    @property
    def media_image_url(self):
        """Image url of current playing media."""
        if self._power == "ON":
            return self._media_image_url
        else:
            return None

    @property
    def media_title(self):
        """Title of current playing media."""
        if self._title is not None:
            return self._title
        else:
            return self._frequency

    @property
    def media_artist(self):
        """Artist of current playing media, music track only."""
        if self._artist is not None:
            return self._artist
        else:
            return self._band

    @property
    def media_album_name(self):
        """Album name of current playing media, music track only."""
        if self._album is not None:
            return self._album
        else:
            return self._station

    @property
    def media_album_artist(self):
        """Album artist of current playing media, music track only."""
        return None

    @property
    def media_track(self):
        """Track number of current playing media, music track only."""
        return None

    @property
    def media_series_title(self):
        """Title of series of current playing media, TV show only."""
        return None

    @property
    def media_season(self):
        """Season of current playing media, TV show only."""
        return None

    @property
    def media_episode(self):
        """Episode of current playing media, TV show only."""
        return None

    def media_play_pause(self):
        """Simulate play pause media player."""
        return self._receiver.toggle_play_pause()

    def media_previous_track(self):
        """Send previous track command."""
        return self._receiver.previous_track()

    def media_next_track(self):
        """Send next track command."""
        return self._receiver.next_track()

    def select_source(self, source):
        """Select input source."""
        return self._receiver.set_input_func(source)

    def turn_on(self):
        """Turn on media player."""
        if self._receiver.power_on():
            self._state = STATE_ON
            return True
        else:
            return False

    def turn_off(self):
        """Turn off media player."""
        if self._receiver.power_off():
            self._state = STATE_OFF
            return True
        else:
            return False

    def volume_up(self):
        """Volume up the media player."""
        return self._receiver.volume_up()

    def volume_down(self):
        """Volume down media player."""
        return self._receiver.volume_down()

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        # Volume has to be sent in a format like -50.0. Minimum is -80.0,
        # maximum is 18.0
        volume_denon = float((volume * 100) - 80)
        if volume_denon > 18:
            volume_denon = float(18)
        try:
            if self._receiver.set_volume(volume_denon):
                self._volume = volume_denon
                return True
            else:
                return False
        except ValueError:
            return False

    def mute_volume(self, mute):
        """Send mute command."""
        return self._receiver.mute(mute)

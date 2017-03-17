"""
Support for interface with an LG webOS Smart TV.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/media_player.webostv/
"""
import logging
from datetime import timedelta
from urllib.parse import urlparse

import voluptuous as vol

import homeassistant.util as util
from homeassistant.components.media_player import (
    SUPPORT_TURN_ON, SUPPORT_TURN_OFF, SUPPORT_PLAY,
    SUPPORT_NEXT_TRACK, SUPPORT_PAUSE, SUPPORT_PREVIOUS_TRACK,
    SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_STEP,
    SUPPORT_SELECT_SOURCE, SUPPORT_PLAY_MEDIA, MEDIA_TYPE_CHANNEL,
    MediaPlayerDevice, PLATFORM_SCHEMA)
from homeassistant.const import (
    CONF_HOST, CONF_MAC, CONF_CUSTOMIZE, STATE_OFF,
    STATE_PLAYING, STATE_PAUSED,
    STATE_UNKNOWN, CONF_NAME)
from homeassistant.loader import get_component
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['https://github.com/TheRealLink/pylgtv'
                '/archive/v0.1.2.zip'
                '#pylgtv==0.1.2',
                'websockets==3.2',
                'wakeonlan==0.2.2']

_CONFIGURING = {}  # type: Dict[str, str]
_LOGGER = logging.getLogger(__name__)

CONF_SOURCES = 'sources'

DEFAULT_NAME = 'LG webOS Smart TV'

SUPPORT_WEBOSTV = SUPPORT_TURN_OFF | \
    SUPPORT_NEXT_TRACK | SUPPORT_PAUSE | SUPPORT_PREVIOUS_TRACK | \
    SUPPORT_VOLUME_MUTE | SUPPORT_VOLUME_STEP | \
    SUPPORT_SELECT_SOURCE | SUPPORT_PLAY_MEDIA | SUPPORT_PLAY

MIN_TIME_BETWEEN_SCANS = timedelta(seconds=10)
MIN_TIME_BETWEEN_FORCED_SCANS = timedelta(seconds=1)

CUSTOMIZE_SCHEMA = vol.Schema({
    vol.Optional(CONF_SOURCES):
        vol.All(cv.ensure_list, [cv.string]),
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_HOST): cv.string,
    vol.Optional(CONF_MAC): cv.string,
    vol.Optional(CONF_CUSTOMIZE, default={}): CUSTOMIZE_SCHEMA,
})


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the LG WebOS TV platform."""
    if discovery_info is not None:
        host = urlparse(discovery_info[1]).hostname
    else:
        host = config.get(CONF_HOST)

    if host is None:
        _LOGGER.error("No TV found in configuration file or with discovery")
        return False

    # Only act if we are not already configuring this host
    if host in _CONFIGURING:
        return

    mac = config.get(CONF_MAC)
    name = config.get(CONF_NAME)
    customize = config.get(CONF_CUSTOMIZE)
    setup_tv(host, mac, name, customize, hass, add_devices)


def setup_tv(host, mac, name, customize, hass, add_devices):
    """Setup a LG WebOS TV based on host parameter."""
    from pylgtv import WebOsClient
    from pylgtv import PyLGTVPairException
    from websockets.exceptions import ConnectionClosed

    client = WebOsClient(host)

    if not client.is_registered():
        if host in _CONFIGURING:
            # Try to pair.
            try:
                client.register()
            except PyLGTVPairException:
                _LOGGER.warning(
                    "Connected to LG webOS TV %s but not paired", host)
                return
            except (OSError, ConnectionClosed):
                _LOGGER.error("Unable to connect to host %s", host)
                return
        else:
            # Not registered, request configuration.
            _LOGGER.warning("LG webOS TV %s needs to be paired", host)
            request_configuration(
                host, mac, name, customize, hass, add_devices)
            return

    # If we came here and configuring this host, mark as done.
    if client.is_registered() and host in _CONFIGURING:
        request_id = _CONFIGURING.pop(host)
        configurator = get_component('configurator')
        configurator.request_done(request_id)

    add_devices([LgWebOSDevice(host, mac, name, customize)], True)


def request_configuration(
        host, mac, name, customize, hass, add_devices):
    """Request configuration steps from the user."""
    configurator = get_component('configurator')

    # We got an error if this method is called while we are configuring
    if host in _CONFIGURING:
        configurator.notify_errors(
            _CONFIGURING[host], 'Failed to pair, please try again.')
        return

    # pylint: disable=unused-argument
    def lgtv_configuration_callback(data):
        """The actions to do when our configuration callback is called."""
        setup_tv(host, mac, name, customize, hass, add_devices)

    _CONFIGURING[host] = configurator.request_config(
        hass, name, lgtv_configuration_callback,
        description='Click start and accept the pairing request on your TV.',
        description_image='/static/images/config_webos.png',
        submit_caption='Start pairing request'
    )


class LgWebOSDevice(MediaPlayerDevice):
    """Representation of a LG WebOS TV."""

    def __init__(self, host, mac, name, customize):
        """Initialize the webos device."""
        from pylgtv import WebOsClient
        from wakeonlan import wol
        self._client = WebOsClient(host)
        self._wol = wol
        self._mac = mac
        self._customize = customize

        self._name = name
        # Assume that the TV is not muted
        self._muted = False
        # Assume that the TV is in Play mode
        self._playing = True
        self._volume = 0
        self._current_source = None
        self._current_source_id = None
        self._state = STATE_UNKNOWN
        self._source_list = {}
        self._app_list = {}

    @util.Throttle(MIN_TIME_BETWEEN_SCANS, MIN_TIME_BETWEEN_FORCED_SCANS)
    def update(self):
        """Retrieve the latest data."""
        from websockets.exceptions import ConnectionClosed
        try:
            self._state = STATE_PLAYING
            self._muted = self._client.get_muted()
            self._volume = self._client.get_volume()
            self._current_source_id = self._client.get_input()
            self._source_list = {}
            self._app_list = {}

            custom_sources = self._customize.get(CONF_SOURCES, [])

            for app in self._client.get_apps():
                self._app_list[app['id']] = app
                if app['id'] == self._current_source_id:
                    self._current_source = app['title']
                    self._source_list[app['title']] = app
                elif (app['id'] in custom_sources or
                      any(word in app['title'] for word in custom_sources) or
                      any(word in app['id'] for word in custom_sources)):
                    self._source_list[app['title']] = app

            for source in self._client.get_inputs():
                if not source['connected']:
                    continue
                app = self._app_list[source['appId']]
                self._source_list[app['title']] = app

        except (OSError, ConnectionClosed):
            self._state = STATE_OFF

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
        return self._volume / 100.0

    @property
    def source(self):
        """Return the current input source."""
        return self._current_source

    @property
    def source_list(self):
        """List of available input sources."""
        return sorted(self._source_list.keys())

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MEDIA_TYPE_CHANNEL

    @property
    def media_image_url(self):
        """Image url of current playing media."""
        if self._current_source_id in self._app_list:
            return self._app_list[self._current_source_id]['largeIcon']
        return None

    @property
    def supported_media_commands(self):
        """Flag of media commands that are supported."""
        if self._mac:
            return SUPPORT_WEBOSTV | SUPPORT_TURN_ON
        return SUPPORT_WEBOSTV

    def turn_off(self):
        """Turn off media player."""
        from websockets.exceptions import ConnectionClosed
        self._state = STATE_OFF
        try:
            self._client.power_off()
        except (OSError, ConnectionClosed):
            pass

    def turn_on(self):
        """Turn on the media player."""
        if self._mac:
            self._wol.send_magic_packet(self._mac)

    def volume_up(self):
        """Volume up the media player."""
        self._client.volume_up()

    def volume_down(self):
        """Volume down media player."""
        self._client.volume_down()

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        tv_volume = volume * 100
        self._client.set_volume(tv_volume)

    def mute_volume(self, mute):
        """Send mute command."""
        self._muted = mute
        self._client.set_mute(mute)

    def media_play_pause(self):
        """Simulate play pause media player."""
        if self._playing:
            self.media_pause()
        else:
            self.media_play()

    def select_source(self, source):
        """Select input source."""
        self._current_source_id = self._source_list[source]['id']
        self._current_source = self._source_list[source]['title']
        self._client.launch_app(self._source_list[source]['id'])

    def media_play(self):
        """Send play command."""
        self._playing = True
        self._state = STATE_PLAYING
        self._client.play()

    def media_pause(self):
        """Send media pause command to media player."""
        self._playing = False
        self._state = STATE_PAUSED
        self._client.pause()

    def media_next_track(self):
        """Send next track command."""
        self._client.fast_forward()

    def media_previous_track(self):
        """Send the previous track command."""
        self._client.rewind()

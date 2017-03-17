"""
Support to interface with Sonos players (via SoCo).

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/media_player.sonos/
"""
import datetime
import logging
from os import path
import socket
import urllib
import voluptuous as vol

from homeassistant.components.media_player import (
    ATTR_MEDIA_ENQUEUE, DOMAIN, MEDIA_TYPE_MUSIC, SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE, SUPPORT_PLAY_MEDIA, SUPPORT_PREVIOUS_TRACK, SUPPORT_SEEK,
    SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_SET, SUPPORT_CLEAR_PLAYLIST,
    SUPPORT_SELECT_SOURCE, MediaPlayerDevice, PLATFORM_SCHEMA, SUPPORT_STOP,
    SUPPORT_PLAY)
from homeassistant.const import (
    STATE_IDLE, STATE_PAUSED, STATE_PLAYING, STATE_OFF, ATTR_ENTITY_ID,
    CONF_HOSTS)
from homeassistant.config import load_yaml_config_file
import homeassistant.helpers.config_validation as cv
from homeassistant.util.dt import utcnow

REQUIREMENTS = ['SoCo==0.12']


_LOGGER = logging.getLogger(__name__)

# The soco library is excessively chatty when it comes to logging and
# causes a LOT of spam in the logs due to making a http connection to each
# speaker every 10 seconds. Quiet it down a bit to just actual problems.
_SOCO_LOGGER = logging.getLogger('soco')
_SOCO_LOGGER.setLevel(logging.ERROR)
_REQUESTS_LOGGER = logging.getLogger('requests')
_REQUESTS_LOGGER.setLevel(logging.ERROR)

SUPPORT_SONOS = SUPPORT_STOP | SUPPORT_PAUSE | SUPPORT_VOLUME_SET |\
    SUPPORT_VOLUME_MUTE | SUPPORT_PREVIOUS_TRACK | SUPPORT_NEXT_TRACK |\
    SUPPORT_PLAY_MEDIA | SUPPORT_SEEK | SUPPORT_CLEAR_PLAYLIST |\
    SUPPORT_SELECT_SOURCE | SUPPORT_PLAY

SERVICE_GROUP_PLAYERS = 'sonos_group_players'
SERVICE_UNJOIN = 'sonos_unjoin'
SERVICE_SNAPSHOT = 'sonos_snapshot'
SERVICE_RESTORE = 'sonos_restore'
SERVICE_SET_TIMER = 'sonos_set_sleep_timer'
SERVICE_CLEAR_TIMER = 'sonos_clear_sleep_timer'

SUPPORT_SOURCE_LINEIN = 'Line-in'
SUPPORT_SOURCE_TV = 'TV'

CONF_ADVERTISE_ADDR = 'advertise_addr'
CONF_INTERFACE_ADDR = 'interface_addr'

# Service call validation schemas
ATTR_SLEEP_TIME = 'sleep_time'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_ADVERTISE_ADDR): cv.string,
    vol.Optional(CONF_INTERFACE_ADDR): cv.string,
    vol.Optional(CONF_HOSTS): vol.All(cv.ensure_list, [cv.string]),
})

SONOS_SCHEMA = vol.Schema({
    ATTR_ENTITY_ID: cv.entity_ids,
})

SONOS_SET_TIMER_SCHEMA = SONOS_SCHEMA.extend({
    vol.Required(ATTR_SLEEP_TIME): vol.All(vol.Coerce(int),
                                           vol.Range(min=0, max=86399))
})

# List of devices that have been registered
DEVICES = []


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Sonos platform."""
    import soco
    global DEVICES

    advertise_addr = config.get(CONF_ADVERTISE_ADDR, None)
    if advertise_addr:
        soco.config.EVENT_ADVERTISE_IP = advertise_addr

    if discovery_info:
        player = soco.SoCo(discovery_info)

        # if device allready exists by config
        if player.uid in [x.unique_id for x in DEVICES]:
            return True

        if player.is_visible:
            device = SonosDevice(hass, player)
            add_devices([device], True)
            if not DEVICES:
                register_services(hass)
            DEVICES.append(device)
            return True
        return False

    players = None
    hosts = config.get(CONF_HOSTS, None)
    if hosts:
        # Support retro compatibility with comma separated list of hosts
        # from config
        hosts = hosts[0] if len(hosts) == 1 else hosts
        hosts = hosts.split(',') if isinstance(hosts, str) else hosts
        players = []
        for host in hosts:
            players.append(soco.SoCo(socket.gethostbyname(host)))

    if not players:
        players = soco.discover(interface_addr=config.get(CONF_INTERFACE_ADDR))

    if not players:
        _LOGGER.warning('No Sonos speakers found.')
        return False

    DEVICES = [SonosDevice(hass, p) for p in players]
    add_devices(DEVICES, True)
    register_services(hass)
    _LOGGER.info('Added %s Sonos speakers', len(players))
    return True


def register_services(hass):
    """Register all services for sonos devices."""
    descriptions = load_yaml_config_file(
        path.join(path.dirname(__file__), 'services.yaml'))

    hass.services.register(DOMAIN, SERVICE_GROUP_PLAYERS,
                           _group_players_service,
                           descriptions.get(SERVICE_GROUP_PLAYERS),
                           schema=SONOS_SCHEMA)

    hass.services.register(DOMAIN, SERVICE_UNJOIN,
                           _unjoin_service,
                           descriptions.get(SERVICE_UNJOIN),
                           schema=SONOS_SCHEMA)

    hass.services.register(DOMAIN, SERVICE_SNAPSHOT,
                           _snapshot_service,
                           descriptions.get(SERVICE_SNAPSHOT),
                           schema=SONOS_SCHEMA)

    hass.services.register(DOMAIN, SERVICE_RESTORE,
                           _restore_service,
                           descriptions.get(SERVICE_RESTORE),
                           schema=SONOS_SCHEMA)

    hass.services.register(DOMAIN, SERVICE_SET_TIMER,
                           _set_sleep_timer_service,
                           descriptions.get(SERVICE_SET_TIMER),
                           schema=SONOS_SET_TIMER_SCHEMA)

    hass.services.register(DOMAIN, SERVICE_CLEAR_TIMER,
                           _clear_sleep_timer_service,
                           descriptions.get(SERVICE_CLEAR_TIMER),
                           schema=SONOS_SCHEMA)


def _apply_service(service, service_func, *service_func_args):
    """Internal func for applying a service."""
    entity_ids = service.data.get('entity_id')

    if entity_ids:
        _devices = [device for device in DEVICES
                    if device.entity_id in entity_ids]
    else:
        _devices = DEVICES

    for device in _devices:
        service_func(device, *service_func_args)
        device.update_ha_state(True)


def _group_players_service(service):
    """Group media players, use player as coordinator."""
    _apply_service(service, SonosDevice.group_players)


def _unjoin_service(service):
    """Unjoin the player from a group."""
    _apply_service(service, SonosDevice.unjoin)


def _snapshot_service(service):
    """Take a snapshot."""
    _apply_service(service, SonosDevice.snapshot)


def _restore_service(service):
    """Restore a snapshot."""
    _apply_service(service, SonosDevice.restore)


def _set_sleep_timer_service(service):
    """Set a timer."""
    _apply_service(service,
                   SonosDevice.set_sleep_timer,
                   service.data[ATTR_SLEEP_TIME])


def _clear_sleep_timer_service(service):
    """Set a timer."""
    _apply_service(service,
                   SonosDevice.clear_sleep_timer)


def only_if_coordinator(func):
    """Decorator for coordinator.

    If used as decorator, avoid calling the decorated method if player is not
    a coordinator. If not, a grouped speaker (not in coordinator role) will
    throw soco.exceptions.SoCoSlaveException.

    Also, partially catch exceptions like:

    soco.exceptions.SoCoUPnPException: UPnP Error 701 received:
    Transition not available from <player ip address>
    """
    def wrapper(*args, **kwargs):
        """Decorator wrapper."""
        if args[0].is_coordinator:
            from soco.exceptions import SoCoUPnPException
            try:
                func(*args, **kwargs)
            except SoCoUPnPException:
                _LOGGER.error('command "%s" for Sonos device "%s" '
                              'not available in this mode',
                              func.__name__, args[0].name)
        else:
            _LOGGER.debug('Ignore command "%s" for Sonos device "%s" (%s)',
                          func.__name__, args[0].name, 'not coordinator')

    return wrapper


def _parse_timespan(timespan):
    """Parse a time-span into number of seconds."""
    if timespan in ('', 'NOT_IMPLEMENTED', None):
        return None
    else:
        return sum(60 ** x[0] * int(x[1]) for x in enumerate(
            reversed(timespan.split(':'))))


class _ProcessSonosEventQueue():
    """Queue like object for dispatching sonos events."""

    def __init__(self, sonos_device):
        self._sonos_device = sonos_device

    def put(self, item, block=True, timeout=None):
        """Queue up event for processing."""
        # Instead of putting events on a queue, dispatch them to the event
        # processing method.
        self._sonos_device.process_sonos_event(item)


class SonosDevice(MediaPlayerDevice):
    """Representation of a Sonos device."""

    def __init__(self, hass, player):
        """Initialize the Sonos device."""
        from soco.snapshot import Snapshot

        self.hass = hass
        self.volume_increment = 5
        self._unique_id = player.uid
        self._player = player
        self._player_volume = None
        self._player_volume_muted = None
        self._speaker_info = None
        self._name = None
        self._status = None
        self._coordinator = None
        self._media_content_id = None
        self._media_duration = None
        self._media_position = None
        self._media_position_updated_at = None
        self._media_image_url = None
        self._media_artist = None
        self._media_album_name = None
        self._media_title = None
        self._media_radio_show = None
        self._media_next_title = None
        self._support_previous_track = False
        self._support_next_track = False
        self._support_stop = False
        self._support_pause = False
        self._current_track_uri = None
        self._current_track_is_radio_stream = False
        self._queue = None
        self._last_avtransport_event = None
        self._is_playing_line_in = None
        self._is_playing_tv = None
        self._favorite_sources = None
        self._source_name = None
        self.soco_snapshot = Snapshot(self._player)

    @property
    def should_poll(self):
        """Polling needed."""
        return True

    @property
    def unique_id(self):
        """Return an unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        if self._coordinator:
            return self._coordinator.state
        if self._status in ('PAUSED_PLAYBACK', 'STOPPED'):
            return STATE_PAUSED
        if self._status in ('PLAYING', 'TRANSITIONING'):
            return STATE_PLAYING
        if self._status == 'OFF':
            return STATE_OFF
        return STATE_IDLE

    @property
    def is_coordinator(self):
        """Return true if player is a coordinator."""
        return self._coordinator is None

    def _is_available(self):
        try:
            sock = socket.create_connection(
                address=(self._player.ip_address, 1443),
                timeout=3)
            sock.close()
            return True
        except socket.error:
            return False

    # pylint: disable=invalid-name
    def _subscribe_to_player_events(self):
        if self._queue is None:
            self._queue = _ProcessSonosEventQueue(self)
            self._player.avTransport.subscribe(
                auto_renew=True,
                event_queue=self._queue)
            self._player.renderingControl.subscribe(
                auto_renew=True,
                event_queue=self._queue)

    # pylint: disable=too-many-branches, too-many-statements
    def update(self):
        """Retrieve latest state."""
        if self._speaker_info is None:
            self._speaker_info = self._player.get_speaker_info(True)
            self._name = self._speaker_info['zone_name'].replace(
                ' (R)', '').replace(' (L)', '')

        if self._last_avtransport_event:
            is_available = True
        else:
            is_available = self._is_available()

        if is_available:

            track_info = None
            if self._last_avtransport_event:
                variables = self._last_avtransport_event.variables
                current_track_metadata = variables.get(
                    'current_track_meta_data', {}
                )

                self._status = variables.get('transport_state')

                if current_track_metadata:
                    # no need to ask speaker for information we already have
                    current_track_metadata = current_track_metadata.__dict__

                    track_info = {
                        'uri': variables.get('current_track_uri'),
                        'artist': current_track_metadata.get('creator'),
                        'album': current_track_metadata.get('album'),
                        'title': current_track_metadata.get('title'),
                        'playlist_position': variables.get('current_track'),
                        'duration': variables.get('current_track_duration')
                    }
            else:
                self._player_volume = self._player.volume
                self._player_volume_muted = self._player.mute
                transport_info = self._player.get_current_transport_info()
                self._status = transport_info.get('current_transport_state')

            if not track_info:
                track_info = self._player.get_current_track_info()

            if track_info['uri'].startswith('x-rincon:'):
                # this speaker is a slave, find the coordinator
                # the uri of the track is 'x-rincon:{coordinator-id}'
                coordinator_id = track_info['uri'][9:]
                coordinators = [device for device in DEVICES
                                if device.unique_id == coordinator_id]
                self._coordinator = coordinators[0] if coordinators else None
            else:
                self._coordinator = None

            if not self._coordinator:

                is_playing_tv = self._player.is_playing_tv
                is_playing_line_in = self._player.is_playing_line_in

                media_info = self._player.avTransport.GetMediaInfo(
                    [('InstanceID', 0)]
                )

                current_media_uri = media_info['CurrentURI']
                media_artist = track_info.get('artist')
                media_album_name = track_info.get('album')
                media_title = track_info.get('title')
                media_image_url = track_info.get('album_art', None)

                media_position = None
                media_position_updated_at = None
                source_name = None

                is_radio_stream = \
                    current_media_uri.startswith('x-sonosapi-stream:') or \
                    current_media_uri.startswith('x-rincon-mp3radio:')

                if is_playing_tv or is_playing_line_in:
                    # playing from line-in/tv.

                    support_previous_track = False
                    support_next_track = False
                    support_stop = False
                    support_pause = False

                    if is_playing_tv:
                        media_artist = SUPPORT_SOURCE_TV
                    else:
                        media_artist = SUPPORT_SOURCE_LINEIN

                    source_name = media_artist

                    media_album_name = None
                    media_title = None
                    media_image_url = None

                elif is_radio_stream:
                    media_image_url = self._format_media_image_url(
                        media_image_url,
                        current_media_uri
                    )
                    support_previous_track = False
                    support_next_track = False
                    support_stop = False
                    support_pause = False

                    source_name = 'Radio'
                    # Check if currently playing radio station is in favorites
                    favs = self._player.get_sonos_favorites()['favorites']
                    favc = [
                        fav for fav in favs if fav['uri'] == current_media_uri
                        ]
                    if len(favc) == 1:
                        src = favc.pop()
                        source_name = src['title']

                    # for radio streams we set the radio station name as the
                    # title.
                    if media_artist and media_title:
                        # artist and album name are in the data, concatenate
                        # that do display as artist.
                        # "Information" field in the sonos pc app

                        media_artist = '{artist} - {title}'.format(
                            artist=media_artist,
                            title=media_title
                        )
                    else:
                        # "On Now" field in the sonos pc app
                        media_artist = self._media_radio_show

                    current_uri_metadata = media_info["CurrentURIMetaData"]
                    if current_uri_metadata not in \
                            ('', 'NOT_IMPLEMENTED', None):

                        # currently soco does not have an API for this
                        import soco
                        current_uri_metadata = soco.xml.XML.fromstring(
                            soco.utils.really_utf8(current_uri_metadata))

                        md_title = current_uri_metadata.findtext(
                            './/{http://purl.org/dc/elements/1.1/}title')

                        if md_title not in ('', 'NOT_IMPLEMENTED', None):
                            media_title = md_title

                    if media_artist and media_title:
                        # some radio stations put their name into the artist
                        # name, e.g.:
                        #   media_title = "Station"
                        #   media_artist = "Station - Artist - Title"
                        # detect this case and trim from the front of
                        # media_artist for cosmetics
                        str_to_trim = '{title} - '.format(
                            title=media_title
                        )
                        chars = min(len(media_artist), len(str_to_trim))

                        if media_artist[:chars].upper() == \
                           str_to_trim[:chars].upper():

                            media_artist = media_artist[chars:]

                else:
                    # not a radio stream
                    media_image_url = self._format_media_image_url(
                        media_image_url,
                        track_info['uri']
                    )
                    support_previous_track = True
                    support_next_track = True
                    support_stop = True
                    support_pause = True

                    position_info = self._player.avTransport.GetPositionInfo(
                        [('InstanceID', 0),
                         ('Channel', 'Master')]
                    )
                    rel_time = _parse_timespan(
                        position_info.get("RelTime")
                    )

                    # player no longer reports position?
                    update_media_position = rel_time is None and \
                        self._media_position is not None

                    # player started reporting position?
                    update_media_position |= rel_time is not None and \
                        self._media_position is None

                    # position changed?
                    if rel_time is not None and \
                       self._media_position is not None:

                        time_diff = utcnow() - self._media_position_updated_at
                        time_diff = time_diff.total_seconds()

                        calculated_position = \
                            self._media_position + \
                            time_diff

                        update_media_position = \
                            abs(calculated_position - rel_time) > 1.5

                    if update_media_position:
                        media_position = rel_time
                        media_position_updated_at = utcnow()
                    else:
                        # don't update media_position (don't want unneeded
                        # state transitions)
                        media_position = self._media_position
                        media_position_updated_at = \
                            self._media_position_updated_at

                    playlist_position = track_info.get('playlist_position')
                    if playlist_position in ('', 'NOT_IMPLEMENTED', None):
                        playlist_position = None
                    else:
                        playlist_position = int(playlist_position)

                    playlist_size = media_info.get('NrTracks')
                    if playlist_size in ('', 'NOT_IMPLEMENTED', None):
                        playlist_size = None
                    else:
                        playlist_size = int(playlist_size)

                    if playlist_position is not None and \
                       playlist_size is not None:

                        if playlist_position == 1:
                            support_previous_track = False

                        if playlist_position == playlist_size:
                            support_next_track = False

                self._media_content_id = track_info.get('title')
                self._media_duration = _parse_timespan(
                    track_info.get('duration')
                )
                self._media_position = media_position
                self._media_position_updated_at = media_position_updated_at
                self._media_image_url = media_image_url
                self._media_artist = media_artist
                self._media_album_name = media_album_name
                self._media_title = media_title
                self._current_track_uri = track_info['uri']
                self._current_track_is_radio_stream = is_radio_stream
                self._support_previous_track = support_previous_track
                self._support_next_track = support_next_track
                self._support_stop = support_stop
                self._support_pause = support_pause
                self._is_playing_tv = is_playing_tv
                self._is_playing_line_in = is_playing_line_in
                self._source_name = source_name

                # update state of the whole group
                # pylint: disable=protected-access
                for device in [x for x in DEVICES if x._coordinator == self]:
                    if device.entity_id is not self.entity_id:
                        self.hass.add_job(device.async_update_ha_state)

                if self._queue is None and self.entity_id is not None:
                    self._subscribe_to_player_events()
            favs = self._player.get_sonos_favorites().get('favorites', [])
            self._favorite_sources = [fav['title'] for fav in favs]
        else:
            self._player_volume = None
            self._player_volume_muted = None
            self._status = 'OFF'
            self._coordinator = None
            self._media_content_id = None
            self._media_duration = None
            self._media_position = None
            self._media_position_updated_at = None
            self._media_image_url = None
            self._media_artist = None
            self._media_album_name = None
            self._media_title = None
            self._media_radio_show = None
            self._media_next_title = None
            self._current_track_uri = None
            self._current_track_is_radio_stream = False
            self._support_previous_track = False
            self._support_next_track = False
            self._support_stop = False
            self._support_pause = False
            self._is_playing_tv = False
            self._is_playing_line_in = False
            self._favorite_sources = None
            self._source_name = None

        self._last_avtransport_event = None

    def _format_media_image_url(self, url, fallback_uri):
        if url in ('', 'NOT_IMPLEMENTED', None):
            return 'http://{host}:{port}/getaa?s=1&u={uri}'.format(
                host=self._player.ip_address,
                port=1400,
                uri=urllib.parse.quote(fallback_uri)
            )
        return url

    def process_sonos_event(self, event):
        """Process a service event coming from the speaker."""
        next_track_image_url = None
        if event.service == self._player.avTransport:
            self._last_avtransport_event = event

            self._media_radio_show = None
            if self._current_track_is_radio_stream:
                current_track_metadata = event.variables.get(
                    'current_track_meta_data'
                )
                if current_track_metadata:
                    self._media_radio_show = \
                        current_track_metadata.radio_show.split(',')[0]

            next_track_uri = event.variables.get('next_track_uri')
            if next_track_uri:
                next_track_image_url = self._format_media_image_url(
                    None,
                    next_track_uri
                )

            next_track_metadata = event.variables.get('next_track_meta_data')
            if next_track_metadata:
                next_track = '{title} - {creator}'.format(
                    title=next_track_metadata.title,
                    creator=next_track_metadata.creator
                )
                if next_track != self._media_next_title:
                    self._media_next_title = next_track
            else:
                self._media_next_title = None

        elif event.service == self._player.renderingControl:
            if 'volume' in event.variables:
                self._player_volume = int(
                    event.variables['volume'].get('Master')
                )

            if 'mute' in event.variables:
                self._player_volume_muted = \
                    event.variables['mute'].get('Master') == '1'

        self.update_ha_state(True)

        if next_track_image_url:
            self.preload_media_image_url(next_track_image_url)

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self._player_volume / 100.0

    @property
    def is_volume_muted(self):
        """Return true if volume is muted."""
        return self._player_volume_muted

    @property
    def media_content_id(self):
        """Content ID of current playing media."""
        if self._coordinator:
            return self._coordinator.media_content_id
        else:
            return self._media_content_id

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MEDIA_TYPE_MUSIC

    @property
    def media_duration(self):
        """Duration of current playing media in seconds."""
        if self._coordinator:
            return self._coordinator.media_duration
        else:
            return self._media_duration

    @property
    def media_position(self):
        """Position of current playing media in seconds."""
        if self._coordinator:
            return self._coordinator.media_position
        else:
            return self._media_position

    @property
    def media_position_updated_at(self):
        """When was the position of the current playing media valid.

        Returns value from homeassistant.util.dt.utcnow().
        """
        if self._coordinator:
            return self._coordinator.media_position_updated_at
        else:
            return self._media_position_updated_at

    @property
    def media_image_url(self):
        """Image url of current playing media."""
        if self._coordinator:
            return self._coordinator.media_image_url
        else:
            return self._media_image_url

    @property
    def media_artist(self):
        """Artist of current playing media, music track only."""
        if self._coordinator:
            return self._coordinator.media_artist
        else:
            return self._media_artist

    @property
    def media_album_name(self):
        """Album name of current playing media, music track only."""
        if self._coordinator:
            return self._coordinator.media_album_name
        else:
            return self._media_album_name

    @property
    def media_title(self):
        """Title of current playing media."""
        if self._coordinator:
            return self._coordinator.media_title
        else:
            return self._media_title

    @property
    def supported_media_commands(self):
        """Flag of media commands that are supported."""
        if self._coordinator:
            return self._coordinator.supported_media_commands

        supported = SUPPORT_SONOS

        if not self._support_previous_track:
            supported = supported ^ SUPPORT_PREVIOUS_TRACK

        if not self._support_next_track:
            supported = supported ^ SUPPORT_NEXT_TRACK

        if not self._support_stop:
            supported = supported ^ SUPPORT_STOP

        if not self._support_pause:
            supported = supported ^ SUPPORT_PAUSE

        return supported

    def volume_up(self):
        """Volume up media player."""
        self._player.volume += self.volume_increment

    def volume_down(self):
        """Volume down media player."""
        self._player.volume -= self.volume_increment

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        self._player.volume = str(int(volume * 100))

    def mute_volume(self, mute):
        """Mute (true) or unmute (false) media player."""
        self._player.mute = mute

    def select_source(self, source):
        """Select input source."""
        if source == SUPPORT_SOURCE_LINEIN:
            self._source_name = SUPPORT_SOURCE_LINEIN
            self._player.switch_to_line_in()
        elif source == SUPPORT_SOURCE_TV:
            self._source_name = SUPPORT_SOURCE_TV
            self._player.switch_to_tv()
        else:
            favorites = self._player.get_sonos_favorites()['favorites']
            fav = [fav for fav in favorites if fav['title'] == source]
            if len(fav) == 1:
                src = fav.pop()
                self._source_name = src['title']
                self._player.play_uri(src['uri'], src['meta'], src['title'])

    @property
    def source_list(self):
        """List of available input sources."""
        model_name = self._speaker_info['model_name']

        sources = self._favorite_sources

        if 'PLAY:5' in model_name:
            sources += [SUPPORT_SOURCE_LINEIN]
        elif 'PLAYBAR' in model_name:
            sources += [SUPPORT_SOURCE_LINEIN, SUPPORT_SOURCE_TV]
        return sources

    @property
    def source(self):
        """Name of the current input source."""
        if self._coordinator:
            return self._coordinator.source
        else:
            return self._source_name

    def turn_off(self):
        """Turn off media player."""
        self.media_pause()

    def media_play(self):
        """Send play command."""
        if self._coordinator:
            self._coordinator.media_play()
        else:
            self._player.play()

    def media_stop(self):
        """Send stop command."""
        if self._coordinator:
            self._coordinator.media_stop()
        else:
            self._player.stop()

    def media_pause(self):
        """Send pause command."""
        if self._coordinator:
            self._coordinator.media_pause()
        else:
            self._player.pause()

    def media_next_track(self):
        """Send next track command."""
        if self._coordinator:
            self._coordinator.media_next_track()
        else:
            self._player.next()

    def media_previous_track(self):
        """Send next track command."""
        if self._coordinator:
            self._coordinator.media_previous_track()
        else:
            self._player.previous()

    def media_seek(self, position):
        """Send seek command."""
        if self._coordinator:
            self._coordinator.media_seek(position)
        else:
            self._player.seek(str(datetime.timedelta(seconds=int(position))))

    def clear_playlist(self):
        """Clear players playlist."""
        if self._coordinator:
            self._coordinator.clear_playlist()
        else:
            self._player.clear_queue()

    def turn_on(self):
        """Turn the media player on."""
        self.media_play()

    def play_media(self, media_type, media_id, **kwargs):
        """
        Send the play_media command to the media player.

        If ATTR_MEDIA_ENQUEUE is True, add `media_id` to the queue.
        """
        if self._coordinator:
            self._coordinator.play_media(media_type, media_id, **kwargs)
        else:
            if kwargs.get(ATTR_MEDIA_ENQUEUE):
                from soco.exceptions import SoCoUPnPException
                try:
                    self._player.add_uri_to_queue(media_id)
                except SoCoUPnPException:
                    _LOGGER.error('Error parsing media uri "%s", '
                                  "please check it's a valid media resource "
                                  'supported by Sonos', media_id)
            else:
                self._player.play_uri(media_id)

    def group_players(self):
        """Group all players under this coordinator."""
        if self._coordinator:
            self._coordinator.group_players()
        else:
            self._player.partymode()

    @only_if_coordinator
    def unjoin(self):
        """Unjoin the player from a group."""
        self._player.unjoin()

    @only_if_coordinator
    def snapshot(self):
        """Snapshot the player."""
        self.soco_snapshot.snapshot()

    @only_if_coordinator
    def restore(self):
        """Restore snapshot for the player."""
        self.soco_snapshot.restore(True)

    @only_if_coordinator
    def set_sleep_timer(self, sleep_time):
        """Set the timer on the player."""
        self._player.set_sleep_timer(sleep_time)

    @only_if_coordinator
    def clear_sleep_timer(self):
        """Clear the timer on the player."""
        self._player.set_sleep_timer(None)

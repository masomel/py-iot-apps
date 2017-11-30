"""
Support for Hikvision event stream events represented as binary sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.hikvision/
"""
import logging
from datetime import timedelta
import voluptuous as vol

from homeassistant.helpers.event import track_point_in_utc_time
from homeassistant.util.dt import utcnow
from homeassistant.components.binary_sensor import (
    BinarySensorDevice, PLATFORM_SCHEMA)
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_HOST, CONF_PORT, CONF_NAME, CONF_USERNAME, CONF_PASSWORD,
    CONF_SSL, EVENT_HOMEASSISTANT_STOP, ATTR_LAST_TRIP_TIME, CONF_CUSTOMIZE)

REQUIREMENTS = ['pyhik==0.0.7', 'pydispatcher==2.0.5']
_LOGGER = logging.getLogger(__name__)

CONF_IGNORED = 'ignored'
CONF_DELAY = 'delay'

DEFAULT_PORT = 80
DEFAULT_IGNORED = False
DEFAULT_DELAY = 0

ATTR_DELAY = 'delay'

SENSOR_CLASS_MAP = {
    'Motion': 'motion',
    'Line Crossing': 'motion',
    'IO Trigger': None,
    'Field Detection': 'motion',
    'Video Loss': None,
    'Tamper Detection': 'motion',
    'Shelter Alarm': None,
    'Disk Full': None,
    'Disk Error': None,
    'Net Interface Broken': 'connectivity',
    'IP Conflict': 'connectivity',
    'Illegal Access': None,
    'Video Mismatch': None,
    'Bad Video': None,
    'PIR Alarm': 'motion',
    'Face Detection': 'motion',
}

CUSTOMIZE_SCHEMA = vol.Schema({
    vol.Optional(CONF_IGNORED, default=DEFAULT_IGNORED): cv.boolean,
    vol.Optional(CONF_DELAY, default=DEFAULT_DELAY): cv.positive_int
    })

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=None): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_SSL, default=False): cv.boolean,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_CUSTOMIZE, default={}):
        vol.Schema({cv.string: CUSTOMIZE_SCHEMA}),
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup Hikvision binary sensor devices."""
    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    customize = config.get(CONF_CUSTOMIZE)

    if config.get(CONF_SSL):
        protocol = "https"
    else:
        protocol = "http"

    url = '{}://{}'.format(protocol, host)

    data = HikvisionData(hass, url, port, name, username, password)

    if data.sensors is None:
        _LOGGER.error('Hikvision event stream has no data, unable to setup.')
        return False

    entities = []

    for sensor in data.sensors:
        # Build sensor name, then parse customize config.
        sensor_name = sensor.replace(' ', '_')

        custom = customize.get(sensor_name.lower(), {})
        ignore = custom.get(CONF_IGNORED)
        delay = custom.get(CONF_DELAY)

        _LOGGER.debug('Entity: %s - %s, Options - Ignore: %s, Delay: %s',
                      data.name, sensor_name, ignore, delay)
        if not ignore:
            entities.append(HikvisionBinarySensor(hass, sensor, data, delay))

    add_entities(entities)


class HikvisionData(object):
    """Hikvision camera event stream object."""

    def __init__(self, hass, url, port, name, username, password):
        """Initialize the data oject."""
        from pyhik.hikvision import HikCamera
        self._url = url
        self._port = port
        self._name = name
        self._username = username
        self._password = password

        # Establish camera
        self._cam = HikCamera(self._url, self._port,
                              self._username, self._password)

        if self._name is None:
            self._name = self._cam.get_name

        # Start event stream
        self._cam.start_stream()

        hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, self.stop_hik)

    def stop_hik(self, event):
        """Shutdown Hikvision subscriptions and subscription thread on exit."""
        self._cam.disconnect()

    @property
    def sensors(self):
        """Return list of available sensors and their states."""
        return self._cam.current_event_states

    @property
    def cam_id(self):
        """Return camera id."""
        return self._cam.get_id

    @property
    def name(self):
        """Return camera name."""
        return self._name


class HikvisionBinarySensor(BinarySensorDevice):
    """Representation of a Hikvision binary sensor."""

    def __init__(self, hass, sensor, cam, delay):
        """Initialize the binary_sensor."""
        from pydispatch import dispatcher

        self._hass = hass
        self._cam = cam
        self._name = self._cam.name + ' ' + sensor
        self._id = self._cam.cam_id + '.' + sensor
        self._sensor = sensor

        if delay is None:
            self._delay = 0
        else:
            self._delay = delay

        self._timer = None

        # Form signal for dispatcher
        signal = 'ValueChanged.{}'.format(self._cam.cam_id)

        dispatcher.connect(self._update_callback,
                           signal=signal,
                           sender=self._sensor)

    def _sensor_state(self):
        """Extract sensor state."""
        return self._cam.sensors[self._sensor][0]

    def _sensor_last_update(self):
        """Extract sensor last update time."""
        return self._cam.sensors[self._sensor][3]

    @property
    def name(self):
        """Return the name of the Hikvision sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return an unique ID."""
        return '{}.{}'.format(self.__class__, self._id)

    @property
    def is_on(self):
        """Return true if sensor is on."""
        return self._sensor_state()

    @property
    def sensor_class(self):
        """Return the class of this sensor, from SENSOR_CLASSES."""
        try:
            return SENSOR_CLASS_MAP[self._sensor]
        except KeyError:
            # Sensor must be unknown to us, add as generic
            return None

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attr = {}
        attr[ATTR_LAST_TRIP_TIME] = self._sensor_last_update()

        if self._delay != 0:
            attr[ATTR_DELAY] = self._delay

        return attr

    def _update_callback(self, signal, sender):
        """Update the sensor's state, if needed."""
        _LOGGER.debug('Dispatcher callback, signal: %s, sender: %s',
                      signal, sender)

        if sender is not self._sensor:
            return

        if self._delay > 0 and not self.is_on:
            # Set timer to wait until updating the state
            def _delay_update(now):
                """Timer callback for sensor update."""
                _LOGGER.debug('%s Called delayed (%ssec) update.',
                              self._name, self._delay)
                self.schedule_update_ha_state()
                self._timer = None

            if self._timer is not None:
                self._timer()
                self._timer = None

            self._timer = track_point_in_utc_time(
                self._hass, _delay_update,
                utcnow() + timedelta(seconds=self._delay))

        elif self._delay > 0 and self.is_on:
            # For delayed sensors kill any callbacks on true events and update
            if self._timer is not None:
                self._timer()
                self._timer = None

            self.schedule_update_ha_state()

        else:
            self.schedule_update_ha_state()

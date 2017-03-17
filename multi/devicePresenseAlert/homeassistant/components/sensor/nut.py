"""
Provides a sensor to track various status aspects of a UPS.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.nut/
"""
import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_HOST, CONF_PORT, CONF_NAME, CONF_USERNAME, CONF_PASSWORD,
    TEMP_CELSIUS, CONF_RESOURCES, CONF_ALIAS, ATTR_STATE, STATE_UNKNOWN)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

REQUIREMENTS = ['pynut2==2.1.2']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'NUT UPS'
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 3493

KEY_STATUS = 'ups.status'

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

SENSOR_TYPES = {
    'ups.status': ['Status Data', '', 'mdi:information-outline'],
    'ups.alarm': ['Alarms', '', 'mdi:alarm'],
    'ups.time': ['Internal Time', '', 'mdi:calendar-clock'],
    'ups.date': ['Internal Date', '', 'mdi:calendar'],
    'ups.model': ['Model', '', 'mdi:information-outline'],
    'ups.mfr': ['Manufacturer', '', 'mdi:information-outline'],
    'ups.mfr.date': ['Manufacture Date', '', 'mdi:calendar'],
    'ups.serial': ['Serial Number', '', 'mdi:information-outline'],
    'ups.vendorid': ['Vendor ID', '', 'mdi:information-outline'],
    'ups.productid': ['Product ID', '', 'mdi:information-outline'],
    'ups.firmware': ['Firmware Version', '', 'mdi:information-outline'],
    'ups.firmware.aux': ['Firmware Version 2', '', 'mdi:information-outline'],
    'ups.temperature': ['UPS Temperature', TEMP_CELSIUS, 'mdi:thermometer'],
    'ups.load': ['Load', '%', 'mdi:gauge'],
    'ups.load.high': ['Overload Setting', '%', 'mdi:gauge'],
    'ups.id': ['System identifier', '', 'mdi:information-outline'],
    'ups.delay.start': ['Load Restart Delay', 'sec', 'mdi:timer'],
    'ups.delay.reboot': ['UPS Reboot Delay', 'sec', 'mdi:timer'],
    'ups.delay.shutdown': ['UPS Shutdown Delay', 'sec', 'mdi:timer'],
    'ups.timer.start': ['Load Start Timer', 'sec', 'mdi:timer'],
    'ups.timer.reboot': ['Load Reboot Timer', 'sec', 'mdi:timer'],
    'ups.timer.shutdown': ['Load Shutdown Timer', 'sec', 'mdi:timer'],
    'ups.test.interval': ['Self-Test Interval', 'sec', 'mdi:timer'],
    'ups.test.result': ['Self-Test Result', '', 'mdi:information-outline'],
    'ups.test.date': ['Self-Test Date', '', 'mdi:calendar'],
    'ups.display.language': ['Language', '', 'mdi:information-outline'],
    'ups.contacts': ['External Contacts', '', 'mdi:information-outline'],
    'ups.efficiency': ['Efficiency', '%', 'mdi:gauge'],
    'ups.power': ['Current Apparent Power', 'VA', 'mdi:flash'],
    'ups.power.nominal': ['Nominal Power', 'VA', 'mdi:flash'],
    'ups.realpower': ['Current Real Power', 'W', 'mdi:flash'],
    'ups.realpower.nominal': ['Nominal Real Power', 'W', 'mdi:flash'],
    'ups.beeper.status': ['Beeper Status', '', 'mdi:information-outline'],
    'ups.type': ['UPS Type', '', 'mdi:information-outline'],
    'ups.watchdog.status': ['Watchdog Status', '', 'mdi:information-outline'],
    'ups.start.auto': ['Start on AC', '', 'mdi:information-outline'],
    'ups.start.battery': ['Start on Battery', '', 'mdi:information-outline'],
    'ups.start.reboot': ['Reboot on Battery', '', 'mdi:information-outline'],
    'ups.shutdown': ['Shutdown Ability', '', 'mdi:information-outline'],
    'battery.charge': ['Battery Charge', '%', 'mdi:gauge'],
    'battery.charge.low': ['Low Battery Setpoint', '%', 'mdi:gauge'],
    'battery.charge.restart': ['Minimum Battery to Start', '%', 'mdi:gauge'],
    'battery.charge.warning': ['Warning Battery Setpoint', '%', 'mdi:gauge'],
    'battery.charger.status':
        ['Charging Status', '', 'mdi:information-outline'],
    'battery.voltage': ['Battery Voltage', 'V', 'mdi:flash'],
    'battery.voltage.nominal': ['Nominal Battery Voltage', 'V', 'mdi:flash'],
    'battery.voltage.low': ['Low Battery Voltage', 'V', 'mdi:flash'],
    'battery.voltage.high': ['High Battery Voltage', 'V', 'mdi:flash'],
    'battery.capacity': ['Battery Capacity', 'Ah', 'mdi:flash'],
    'battery.current': ['Battery Current', 'A', 'mdi:flash'],
    'battery.current.total': ['Total Battery Current', 'A', 'mdi:flash'],
    'battery.temperature':
        ['Battery Temperature', TEMP_CELSIUS, 'mdi:thermometer'],
    'battery.runtime': ['Battery Runtime', 'sec', 'mdi:timer'],
    'battery.runtime.low': ['Low Battery Runtime', 'sec', 'mdi:timer'],
    'battery.runtime.restart':
        ['Minimum Battery Runtime to Start', 'sec', 'mdi:timer'],
    'battery.alarm.threshold':
        ['Battery Alarm Threshold', '', 'mdi:information-outline'],
    'battery.date': ['Battery Date', '', 'mdi:calendar'],
    'battery.mfr.date': ['Battery Manuf. Date', '', 'mdi:calendar'],
    'battery.packs': ['Number of Batteries', '', 'mdi:information-outline'],
    'battery.packs.bad':
        ['Number of Bad Batteries', '', 'mdi:information-outline'],
    'battery.type': ['Battery Chemistry', '', 'mdi:information-outline'],
    'input.sensitivity':
        ['Input Power Sensitivity', '', 'mdi:information-outline'],
    'input.transfer.low': ['Low Voltage Transfer', 'V', 'mdi:flash'],
    'input.transfer.high': ['High Voltage Transfer', 'V', 'mdi:flash'],
    'input.transfer.reason':
        ['Voltage Transfer Reason', '', 'mdi:information-outline'],
    'input.voltage': ['Input Voltage', 'V', 'mdi:flash'],
    'input.voltage.nominal': ['Nominal Input Voltage', 'V', 'mdi:flash'],
}

STATE_TYPES = {
    'OL': 'Online',
    'OB': 'On Battery',
    'LB': 'Low Battery',
    'HB': 'High Battery',
    'RB': 'Battery Needs Replaced',
    'CHRG': 'Battery Charging',
    'BYPASS': 'Bypass Active',
    'CAL': 'Runtime Calibration',
    'OFF': 'Offline',
    'OVER': 'Overloaded',
    'TRIM': 'Trimming Voltage',
    'BOOST': 'Boosting Voltage',
    'FSD': 'Forced Shutdown',
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_ALIAS, default=None): cv.string,
    vol.Optional(CONF_USERNAME, default=None): cv.string,
    vol.Optional(CONF_PASSWORD, default=None): cv.string,
    vol.Required(CONF_RESOURCES, default=[]):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the NUT sensors."""
    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)
    alias = config.get(CONF_ALIAS)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    data = PyNUTData(host, port, alias, username, password)

    if data.status is None:
        _LOGGER.error("NUT Sensor has no data, unable to setup.")
        return False

    _LOGGER.debug('NUT Sensors Available: %s', data.status)

    entities = []

    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()

        if sensor_type in data.status:
            entities.append(NUTSensor(name, data, sensor_type))
        else:
            _LOGGER.warning(
                'Sensor type: "%s" does not appear in the NUT status '
                'output, cannot add.', sensor_type)

    try:
        data.update(no_throttle=True)
    except data.pynuterror as err:
        _LOGGER.error("Failure while testing NUT status retrieval. "
                      "Cannot continue setup., %s", err)
        return False

    add_entities(entities)


class NUTSensor(Entity):
    """Representation of a sensor entity for NUT status values."""

    def __init__(self, name, data, sensor_type):
        """Initialize the sensor."""
        self._data = data
        self.type = sensor_type
        self._name = name + ' ' + SENSOR_TYPES[sensor_type][0]
        self._unit = SENSOR_TYPES[sensor_type][1]
        self.update()

    @property
    def name(self):
        """Return the name of the UPS sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return SENSOR_TYPES[self.type][2]

    @property
    def state(self):
        """Return entity state from ups."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    @property
    def device_state_attributes(self):
        """Return the sensor attributes."""
        attr = {}
        attr[ATTR_STATE] = self.opp_state()
        return attr

    def opp_state(self):
        """Return UPS operating state."""
        if self._data.status is None:
            return STATE_TYPES['OFF']
        else:
            try:
                return STATE_TYPES[self._data.status[KEY_STATUS]]
            except KeyError:
                return STATE_UNKNOWN

    def update(self):
        """Get the latest status and use it to update our sensor state."""
        if self._data.status is None:
            self._state = None
            return

        if self.type not in self._data.status:
            self._state = None
        else:
            self._state = self._data.status[self.type]


class PyNUTData(object):
    """Stores the data retrieved from NUT.

    For each entity to use, acts as the single point responsible for fetching
    updates from the server.
    """

    def __init__(self, host, port, alias, username, password):
        """Initialize the data oject."""
        from pynut2.nut2 import PyNUTClient, PyNUTError
        self._host = host
        self._port = port
        self._alias = alias
        self._username = username
        self._password = password

        self.pynuterror = PyNUTError
        # Establish client with persistent=False to open/close connection on
        # each update call.  This is more reliable with async.
        self._client = PyNUTClient(self._host, self._port,
                                   self._username, self._password, 5, False)

        self._status = None

    @property
    def status(self):
        """Get latest update if throttle allows. Return status."""
        self.update()
        return self._status

    def _get_alias(self):
        """Get the ups alias from NUT."""
        try:
            return next(iter(self._client.list_ups()))
        except self.pynuterror as err:
            _LOGGER.error("Failure getting NUT ups alias, %s", err)
            return None

    def _get_status(self):
        """Get the ups status from NUT."""
        if self._alias is None:
            self._alias = self._get_alias()

        try:
            return self._client.list_vars(self._alias)
        except (self.pynuterror, ConnectionResetError) as err:
            _LOGGER.debug("Error getting NUT vars for host %s: %s",
                          self._host, err)
            return None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self, **kwargs):
        """Fetch the latest status from APCUPSd."""
        self._status = self._get_status()

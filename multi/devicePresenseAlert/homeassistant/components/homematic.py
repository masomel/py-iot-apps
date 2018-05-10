"""
Support for Homematic devices.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/homematic/
"""
import os
import time
import logging
from datetime import timedelta
from functools import partial

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    EVENT_HOMEASSISTANT_STOP, STATE_UNKNOWN, CONF_USERNAME, CONF_PASSWORD,
    CONF_PLATFORM, CONF_HOSTS, CONF_NAME, ATTR_ENTITY_ID)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers import discovery
from homeassistant.config import load_yaml_config_file
from homeassistant.util import Throttle

DOMAIN = 'homematic'
REQUIREMENTS = ["pyhomematic==0.1.18"]

MIN_TIME_BETWEEN_UPDATE_HUB = timedelta(seconds=300)
MIN_TIME_BETWEEN_UPDATE_VAR = timedelta(seconds=30)

DISCOVER_SWITCHES = 'homematic.switch'
DISCOVER_LIGHTS = 'homematic.light'
DISCOVER_SENSORS = 'homematic.sensor'
DISCOVER_BINARY_SENSORS = 'homematic.binary_sensor'
DISCOVER_COVER = 'homematic.cover'
DISCOVER_CLIMATE = 'homematic.climate'

ATTR_DISCOVER_DEVICES = 'devices'
ATTR_PARAM = 'param'
ATTR_CHANNEL = 'channel'
ATTR_NAME = 'name'
ATTR_ADDRESS = 'address'
ATTR_VALUE = 'value'
ATTR_PROXY = 'proxy'

EVENT_KEYPRESS = 'homematic.keypress'
EVENT_IMPULSE = 'homematic.impulse'

SERVICE_VIRTUALKEY = 'virtualkey'
SERVICE_RECONNECT = 'reconnect'
SERVICE_SET_VAR_VALUE = 'set_var_value'
SERVICE_SET_DEV_VALUE = 'set_dev_value'

HM_DEVICE_TYPES = {
    DISCOVER_SWITCHES: [
        'Switch', 'SwitchPowermeter', 'IOSwitch', 'IPSwitch',
        'IPSwitchPowermeter', 'KeyMatic'],
    DISCOVER_LIGHTS: ['Dimmer', 'KeyDimmer'],
    DISCOVER_SENSORS: [
        'SwitchPowermeter', 'Motion', 'MotionV2', 'RemoteMotion',
        'ThermostatWall', 'AreaThermostat', 'RotaryHandleSensor',
        'WaterSensor', 'PowermeterGas', 'LuxSensor', 'WeatherSensor',
        'WeatherStation', 'ThermostatWall2', 'TemperatureDiffSensor',
        'TemperatureSensor', 'CO2Sensor', 'IPSwitchPowermeter'],
    DISCOVER_CLIMATE: [
        'Thermostat', 'ThermostatWall', 'MAXThermostat', 'ThermostatWall2'],
    DISCOVER_BINARY_SENSORS: [
        'ShutterContact', 'Smoke', 'SmokeV2', 'Motion', 'MotionV2',
        'RemoteMotion', 'WeatherSensor', 'TiltSensor', 'IPShutterContact'],
    DISCOVER_COVER: ['Blind', 'KeyBlind']
}

HM_IGNORE_DISCOVERY_NODE = [
    'ACTUAL_TEMPERATURE',
    'ACTUAL_HUMIDITY'
]

HM_ATTRIBUTE_SUPPORT = {
    'LOWBAT': ['Battery', {0: 'High', 1: 'Low'}],
    'ERROR': ['Sabotage', {0: 'No', 1: 'Yes'}],
    'RSSI_DEVICE': ['RSSI', {}],
    'VALVE_STATE': ['Valve', {}],
    'BATTERY_STATE': ['Battery', {}],
    'CONTROL_MODE': ['Mode', {0: 'Auto', 1: 'Manual', 2: 'Away', 3: 'Boost'}],
    'POWER': ['Power', {}],
    'CURRENT': ['Current', {}],
    'VOLTAGE': ['Voltage', {}],
    'WORKING': ['Working', {0: 'No', 1: 'Yes'}],
}

HM_PRESS_EVENTS = [
    'PRESS_SHORT',
    'PRESS_LONG',
    'PRESS_CONT',
    'PRESS_LONG_RELEASE',
    'PRESS',
]

HM_IMPULSE_EVENTS = [
    'SEQUENCE_OK',
]

_LOGGER = logging.getLogger(__name__)

CONF_RESOLVENAMES_OPTIONS = [
    'metadata',
    'json',
    'xml',
    False
]

DATA_HOMEMATIC = 'homematic'
DATA_DELAY = 'homematic_delay'
DATA_DEVINIT = 'homematic_devinit'
DATA_STORE = 'homematic_store'

CONF_LOCAL_IP = 'local_ip'
CONF_LOCAL_PORT = 'local_port'
CONF_IP = 'ip'
CONF_PORT = 'port'
CONF_RESOLVENAMES = 'resolvenames'
CONF_VARIABLES = 'variables'
CONF_DEVICES = 'devices'
CONF_DELAY = 'delay'
CONF_PRIMARY = 'primary'

DEFAULT_LOCAL_IP = "0.0.0.0"
DEFAULT_LOCAL_PORT = 0
DEFAULT_RESOLVENAMES = False
DEFAULT_PORT = 2001
DEFAULT_USERNAME = "Admin"
DEFAULT_PASSWORD = ""
DEFAULT_VARIABLES = False
DEFAULT_DEVICES = True
DEFAULT_DELAY = 0.5
DEFAULT_PRIMARY = False


DEVICE_SCHEMA = vol.Schema({
    vol.Required(CONF_PLATFORM): "homematic",
    vol.Required(ATTR_NAME): cv.string,
    vol.Required(ATTR_ADDRESS): cv.string,
    vol.Required(ATTR_PROXY): cv.string,
    vol.Optional(ATTR_CHANNEL, default=1): vol.Coerce(int),
    vol.Optional(ATTR_PARAM): cv.string,
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOSTS): {cv.match_all: {
            vol.Required(CONF_IP): cv.string,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT):
                cv.port,
            vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): cv.string,
            vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD): cv.string,
            vol.Optional(CONF_VARIABLES, default=DEFAULT_VARIABLES):
                cv.boolean,
            vol.Optional(CONF_RESOLVENAMES, default=DEFAULT_RESOLVENAMES):
                vol.In(CONF_RESOLVENAMES_OPTIONS),
            vol.Optional(CONF_DEVICES, default=DEFAULT_DEVICES): cv.boolean,
            vol.Optional(CONF_PRIMARY, default=DEFAULT_PRIMARY): cv.boolean,
        }},
        vol.Optional(CONF_LOCAL_IP, default=DEFAULT_LOCAL_IP): cv.string,
        vol.Optional(CONF_LOCAL_PORT, default=DEFAULT_LOCAL_PORT): cv.port,
        vol.Optional(CONF_DELAY, default=DEFAULT_DELAY): vol.Coerce(float),
    }),
}, extra=vol.ALLOW_EXTRA)

SCHEMA_SERVICE_VIRTUALKEY = vol.Schema({
    vol.Required(ATTR_ADDRESS): cv.string,
    vol.Required(ATTR_CHANNEL): vol.Coerce(int),
    vol.Required(ATTR_PARAM): cv.string,
    vol.Optional(ATTR_PROXY): cv.string,
})

SCHEMA_SERVICE_SET_VAR_VALUE = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_VALUE): cv.match_all,
})

SCHEMA_SERVICE_SET_DEV_VALUE = vol.Schema({
    vol.Required(ATTR_ADDRESS): cv.string,
    vol.Required(ATTR_CHANNEL): vol.Coerce(int),
    vol.Required(ATTR_PARAM): cv.string,
    vol.Required(ATTR_VALUE): cv.match_all,
    vol.Optional(ATTR_PROXY): cv.string,
})

SCHEMA_SERVICE_RECONNECT = vol.Schema({})


def virtualkey(hass, address, channel, param, proxy=None):
    """Send virtual keypress to homematic controlller."""
    data = {
        ATTR_ADDRESS: address,
        ATTR_CHANNEL: channel,
        ATTR_PARAM: param,
        ATTR_PROXY: proxy,
    }

    hass.services.call(DOMAIN, SERVICE_VIRTUALKEY, data)


def set_var_value(hass, entity_id, value):
    """Change value of homematic system variable."""
    data = {
        ATTR_ENTITY_ID: entity_id,
        ATTR_VALUE: value,
    }

    hass.services.call(DOMAIN, SERVICE_SET_VAR_VALUE, data)


def set_dev_value(hass, address, channel, param, value, proxy=None):
    """Send virtual keypress to homematic controlller."""
    data = {
        ATTR_ADDRESS: address,
        ATTR_CHANNEL: channel,
        ATTR_PARAM: param,
        ATTR_VALUE: value,
        ATTR_PROXY: proxy,
    }

    hass.services.call(DOMAIN, SERVICE_SET_DEV_VALUE, data)


def reconnect(hass):
    """Reconnect to CCU/Homegear."""
    hass.services.call(DOMAIN, SERVICE_RECONNECT, {})


# pylint: disable=unused-argument
def setup(hass, config):
    """Setup the Homematic component."""
    from pyhomematic import HMConnection

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    hass.data[DATA_DELAY] = config[DOMAIN].get(CONF_DELAY)
    hass.data[DATA_DEVINIT] = {}
    hass.data[DATA_STORE] = []

    # create hosts list for pyhomematic
    remotes = {}
    hosts = {}
    for rname, rconfig in list(config[DOMAIN][CONF_HOSTS].items()):
        server = rconfig.get(CONF_IP)

        remotes[rname] = {}
        remotes[rname][CONF_IP] = server
        remotes[rname][CONF_PORT] = rconfig.get(CONF_PORT)
        remotes[rname][CONF_RESOLVENAMES] = rconfig.get(CONF_RESOLVENAMES)
        remotes[rname][CONF_USERNAME] = rconfig.get(CONF_USERNAME)
        remotes[rname][CONF_PASSWORD] = rconfig.get(CONF_PASSWORD)

        if server not in hosts or rconfig.get(CONF_PRIMARY):
            hosts[server] = {
                CONF_VARIABLES: rconfig.get(CONF_VARIABLES),
                CONF_NAME: rname,
            }
        hass.data[DATA_DEVINIT][rname] = rconfig.get(CONF_DEVICES)

    # Create server thread
    bound_system_callback = partial(_system_callback_handler, hass, config)
    hass.data[DATA_HOMEMATIC] = HMConnection(
        local=config[DOMAIN].get(CONF_LOCAL_IP),
        localport=config[DOMAIN].get(CONF_LOCAL_PORT),
        remotes=remotes,
        systemcallback=bound_system_callback,
        interface_id="homeassistant"
    )

    # Start server thread, connect to peer, initialize to receive events
    hass.data[DATA_HOMEMATIC].start()

    # Stops server when Homeassistant is shutting down
    hass.bus.listen_once(
        EVENT_HOMEASSISTANT_STOP, hass.data[DATA_HOMEMATIC].stop)
    hass.config.components.append(DOMAIN)

    # init homematic hubs
    hub_entities = []
    for _, hub_data in list(hosts.items()):
        hub_entities.append(HMHub(hass, component, hub_data[CONF_NAME],
                                  hub_data[CONF_VARIABLES]))
    component.add_entities(hub_entities)

    # regeister homematic services
    descriptions = load_yaml_config_file(
        os.path.join(os.path.dirname(__file__), 'services.yaml'))

    def _hm_service_virtualkey(service):
        """Service handle virtualkey services."""
        address = service.data.get(ATTR_ADDRESS)
        channel = service.data.get(ATTR_CHANNEL)
        param = service.data.get(ATTR_PARAM)

        # device not found
        hmdevice = _device_from_servicecall(hass, service)
        if hmdevice is None:
            _LOGGER.error("%s not found for service virtualkey!", address)
            return

        # if param exists for this device
        if param not in hmdevice.ACTIONNODE:
            _LOGGER.error("%s not datapoint in hm device %s", param, address)
            return

        # channel exists?
        if channel not in hmdevice.ACTIONNODE[param]:
            _LOGGER.error("%i is not a channel in hm device %s",
                          channel, address)
            return

        # call key
        hmdevice.actionNodeData(param, True, channel)

    hass.services.register(
        DOMAIN, SERVICE_VIRTUALKEY, _hm_service_virtualkey,
        descriptions[DOMAIN][SERVICE_VIRTUALKEY],
        schema=SCHEMA_SERVICE_VIRTUALKEY)

    def _service_handle_value(service):
        """Set value on homematic variable object."""
        variable_list = component.extract_from_service(service)

        value = service.data[ATTR_VALUE]

        for hm_variable in variable_list:
            if isinstance(hm_variable, HMVariable):
                hm_variable.hm_set(value)

    hass.services.register(
        DOMAIN, SERVICE_SET_VAR_VALUE, _service_handle_value,
        descriptions[DOMAIN][SERVICE_SET_VAR_VALUE],
        schema=SCHEMA_SERVICE_SET_VAR_VALUE)

    def _service_handle_reconnect(service):
        """Reconnect to all homematic hubs."""
        hass.data[DATA_HOMEMATIC].reconnect()

    hass.services.register(
        DOMAIN, SERVICE_RECONNECT, _service_handle_reconnect,
        descriptions[DOMAIN][SERVICE_RECONNECT],
        schema=SCHEMA_SERVICE_RECONNECT)

    def _service_handle_device(service):
        """Service handle set_dev_value services."""
        address = service.data.get(ATTR_ADDRESS)
        channel = service.data.get(ATTR_CHANNEL)
        param = service.data.get(ATTR_PARAM)
        value = service.data.get(ATTR_VALUE)

        # device not found
        hmdevice = _device_from_servicecall(hass, service)
        if hmdevice is None:
            _LOGGER.error("%s not found!", address)
            return

        # call key
        hmdevice.setValue(param, value, channel)

    hass.services.register(
        DOMAIN, SERVICE_SET_DEV_VALUE, _service_handle_device,
        descriptions[DOMAIN][SERVICE_SET_DEV_VALUE],
        schema=SCHEMA_SERVICE_SET_DEV_VALUE)

    return True


def _system_callback_handler(hass, config, src, *args):
    """Callback handler."""
    if src == 'newDevices':
        _LOGGER.debug("newDevices with: %s", args)
        # pylint: disable=unused-variable
        (interface_id, dev_descriptions) = args
        proxy = interface_id.split('-')[-1]

        # device support active?
        if not hass.data[DATA_DEVINIT][proxy]:
            return

        ##
        # Get list of all keys of the devices (ignoring channels)
        key_dict = {}
        for dev in dev_descriptions:
            key_dict[dev['ADDRESS'].split(':')[0]] = True

        ##
        # remove device they allready init by HA
        tmp_devs = key_dict.copy()
        for dev in tmp_devs:
            if dev in hass.data[DATA_STORE]:
                del key_dict[dev]
            else:
                hass.data[DATA_STORE].append(dev)

        # Register EVENTS
        # Search all device with a EVENTNODE that include data
        bound_event_callback = partial(_hm_event_handler, hass, proxy)
        for dev in key_dict:
            hmdevice = hass.data[DATA_HOMEMATIC].devices[proxy].get(dev)

            # have events?
            if len(hmdevice.EVENTNODE) > 0:
                _LOGGER.debug("Register Events from %s", dev)
                hmdevice.setEventCallback(callback=bound_event_callback,
                                          bequeath=True)

        # If configuration allows autodetection of devices,
        # all devices not configured are added.
        if key_dict:
            for component_name, discovery_type in (
                    ('switch', DISCOVER_SWITCHES),
                    ('light', DISCOVER_LIGHTS),
                    ('cover', DISCOVER_COVER),
                    ('binary_sensor', DISCOVER_BINARY_SENSORS),
                    ('sensor', DISCOVER_SENSORS),
                    ('climate', DISCOVER_CLIMATE)):
                # Get all devices of a specific type
                found_devices = _get_devices(
                    hass, discovery_type, key_dict, proxy)

                # When devices of this type are found
                # they are setup in HA and an event is fired
                if found_devices:
                    # Fire discovery event
                    discovery.load_platform(hass, component_name, DOMAIN, {
                        ATTR_DISCOVER_DEVICES: found_devices
                    }, config)


def _get_devices(hass, device_type, keys, proxy):
    """Get the Homematic devices."""
    device_arr = []

    for key in keys:
        device = hass.data[DATA_HOMEMATIC].devices[proxy][key]
        class_name = device.__class__.__name__
        metadata = {}

        # is class supported by discovery type
        if class_name not in HM_DEVICE_TYPES[device_type]:
            continue

        # Load metadata if needed to generate a param list
        if device_type == DISCOVER_SENSORS:
            metadata.update(device.SENSORNODE)
        elif device_type == DISCOVER_BINARY_SENSORS:
            metadata.update(device.BINARYNODE)
        else:
            metadata.update({None: device.ELEMENT})

        if metadata:
            # Generate options for 1...n elements with 1...n params
            for param, channels in list(metadata.items()):
                if param in HM_IGNORE_DISCOVERY_NODE:
                    continue

                # add devices
                _LOGGER.debug("Handling %s: %s", param, channels)
                for channel in channels:
                    name = _create_ha_name(
                        name=device.NAME,
                        channel=channel,
                        param=param,
                        count=len(channels)
                    )
                    device_dict = {
                        CONF_PLATFORM: "homematic",
                        ATTR_ADDRESS: key,
                        ATTR_PROXY: proxy,
                        ATTR_NAME: name,
                        ATTR_CHANNEL: channel
                    }
                    if param is not None:
                        device_dict[ATTR_PARAM] = param

                    # Add new device
                    try:
                        DEVICE_SCHEMA(device_dict)
                        device_arr.append(device_dict)
                    except vol.MultipleInvalid as err:
                        _LOGGER.error("Invalid device config: %s",
                                      str(err))
        else:
            _LOGGER.debug("Got no params for %s", key)
    _LOGGER.debug("%s autodiscovery: %s", device_type, str(device_arr))
    return device_arr


def _create_ha_name(name, channel, param, count):
    """Generate a unique object name."""
    # HMDevice is a simple device
    if count == 1 and param is None:
        return name

    # Has multiple elements/channels
    if count > 1 and param is None:
        return "{} {}".format(name, channel)

    # With multiple param first elements
    if count == 1 and param is not None:
        return "{} {}".format(name, param)

    # Multiple param on object with multiple elements
    if count > 1 and param is not None:
        return "{} {} {}".format(name, channel, param)


def setup_hmdevice_discovery_helper(hass, hmdevicetype, discovery_info,
                                    add_callback_devices):
    """Helper to setup Homematic devices with discovery info."""
    devices = []
    for config in discovery_info[ATTR_DISCOVER_DEVICES]:
        _LOGGER.debug("Add device %s from config: %s",
                      str(hmdevicetype), str(config))

        # create object and add to HA
        new_device = hmdevicetype(hass, config)
        new_device.link_homematic()
        devices.append(new_device)

    add_callback_devices(devices)
    return True


def _hm_event_handler(hass, proxy, device, caller, attribute, value):
    """Handle all pyhomematic device events."""
    try:
        channel = int(device.split(":")[1])
        address = device.split(":")[0]
        hmdevice = hass.data[DATA_HOMEMATIC].devices[proxy].get(address)
    except (TypeError, ValueError):
        _LOGGER.error("Event handling channel convert error!")
        return

    # is not a event?
    if attribute not in hmdevice.EVENTNODE:
        return

    _LOGGER.debug("Event %s for %s channel %i", attribute,
                  hmdevice.NAME, channel)

    # keypress event
    if attribute in HM_PRESS_EVENTS:
        hass.add_job(hass.bus.async_fire(EVENT_KEYPRESS, {
            ATTR_NAME: hmdevice.NAME,
            ATTR_PARAM: attribute,
            ATTR_CHANNEL: channel
        }))
        return

    # impulse event
    if attribute in HM_IMPULSE_EVENTS:
        hass.add_job(hass.bus.async_fire(EVENT_KEYPRESS, {
            ATTR_NAME: hmdevice.NAME,
            ATTR_CHANNEL: channel
        }))
        return

    _LOGGER.warning("Event is unknown and not forwarded to HA")


def _device_from_servicecall(hass, service):
    """Extract homematic device from service call."""
    address = service.data.get(ATTR_ADDRESS)
    proxy = service.data.get(ATTR_PROXY)

    if proxy:
        return hass.data[DATA_HOMEMATIC].devices[proxy].get(address)

    for _, devices in list(hass.data[DATA_HOMEMATIC].devices.items()):
        if address in devices:
            return devices[address]


class HMHub(Entity):
    """The Homematic hub. I.e. CCU2/HomeGear."""

    def __init__(self, hass, component, name, use_variables):
        """Initialize Homematic hub."""
        self.hass = hass
        self._homematic = hass.data[DATA_HOMEMATIC]
        self._component = component
        self._name = name
        self._state = STATE_UNKNOWN
        self._store = {}
        self._use_variables = use_variables

        # load data
        self._update_hub_state()
        self._init_variables()

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the entity."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        return {}

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return "mdi:gradient"

    def update(self):
        """Update Hub data and all HM variables."""
        self._update_hub_state()
        self._update_variables_state()

    @Throttle(MIN_TIME_BETWEEN_UPDATE_HUB)
    def _update_hub_state(self):
        """Retrieve latest state."""
        state = self._homematic.getServiceMessages(self._name)
        self._state = STATE_UNKNOWN if state is None else len(state)

    @Throttle(MIN_TIME_BETWEEN_UPDATE_VAR)
    def _update_variables_state(self):
        """Retrive all variable data and update hmvariable states."""
        if not self._use_variables:
            return

        variables = self._homematic.getAllSystemVariables(self._name)
        if variables is None:
            return

        for key, value in list(variables.items()):
            if key in self._store:
                self._store.get(key).hm_update(value)

    def _init_variables(self):
        """Load variables from hub."""
        if not self._use_variables:
            return

        variables = self._homematic.getAllSystemVariables(self._name)
        if variables is None:
            return

        entities = []
        for key, value in list(variables.items()):
            entities.append(HMVariable(self.hass, self._name, key, value))
        self._component.add_entities(entities)


class HMVariable(Entity):
    """The Homematic system variable."""

    def __init__(self, hass, hub_name, name, state):
        """Initialize Homematic hub."""
        self.hass = hass
        self._homematic = hass.data[DATA_HOMEMATIC]
        self._state = state
        self._name = name
        self._hub_name = hub_name

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the entity."""
        return self._state

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return "mdi:code-string"

    @property
    def should_poll(self):
        """Return false. Homematic Hub object update variable."""
        return False

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        attr = {
            'hub': self._hub_name,
        }
        return attr

    def hm_update(self, value):
        """Update variable over Hub object."""
        if value != self._state:
            self._state = value
            self.schedule_update_ha_state()

    def hm_set(self, value):
        """Set variable on homematic controller."""
        if isinstance(self._state, bool):
            value = cv.boolean(value)
        else:
            value = float(value)
        self._homematic.setSystemVariable(self._hub_name, self._name, value)
        self._state = value
        self.schedule_update_ha_state()


class HMDevice(Entity):
    """The Homematic device base object."""

    def __init__(self, hass, config):
        """Initialize a generic Homematic device."""
        self.hass = hass
        self._homematic = hass.data[DATA_HOMEMATIC]
        self._name = config.get(ATTR_NAME)
        self._address = config.get(ATTR_ADDRESS)
        self._proxy = config.get(ATTR_PROXY)
        self._channel = config.get(ATTR_CHANNEL)
        self._state = config.get(ATTR_PARAM)
        self._data = {}
        self._hmdevice = None
        self._connected = False
        self._available = False

        # Set param to uppercase
        if self._state:
            self._state = self._state.upper()

    @property
    def should_poll(self):
        """Return false. Homematic states are pushed by the XML RPC Server."""
        return False

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def assumed_state(self):
        """Return true if unable to access real state of the device."""
        return not self._available

    @property
    def available(self):
        """Return true if device is available."""
        return self._available

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        attr = {}

        # no data available to create
        if not self.available:
            return attr

        # Generate an attributes list
        for node, data in list(HM_ATTRIBUTE_SUPPORT.items()):
            # Is an attributes and exists for this object
            if node in self._data:
                value = data[1].get(self._data[node], self._data[node])
                attr[data[0]] = value

        # static attributes
        attr['ID'] = self._hmdevice.ADDRESS
        attr['proxy'] = self._proxy

        return attr

    def link_homematic(self):
        """Connect to Homematic."""
        # device is already linked
        if self._connected:
            return True

        # Init
        self._hmdevice = self._homematic.devices[self._proxy][self._address]
        self._connected = True

        # Check if Homematic class is okay for HA class
        _LOGGER.info("Start linking %s to %s", self._address, self._name)
        try:
            # Init datapoints of this object
            self._init_data()
            if self.hass.data[DATA_DELAY]:
                # We delay / pause loading of data to avoid overloading
                # of CCU / Homegear when doing auto detection
                time.sleep(self.hass.data[DATA_DELAY])
            self._load_data_from_hm()
            _LOGGER.debug("%s datastruct: %s", self._name, str(self._data))

            # Link events from pyhomatic
            self._subscribe_homematic_events()
            self._available = not self._hmdevice.UNREACH
            _LOGGER.debug("%s linking done", self._name)
        # pylint: disable=broad-except
        except Exception as err:
            self._connected = False
            _LOGGER.error("Exception while linking %s: %s",
                          self._address, str(err))

    def _hm_event_callback(self, device, caller, attribute, value):
        """Handle all pyhomematic device events."""
        _LOGGER.debug("%s received event '%s' value: %s", self._name,
                      attribute, value)
        have_change = False

        # Is data needed for this instance?
        if attribute in self._data:
            # Did data change?
            if self._data[attribute] != value:
                self._data[attribute] = value
                have_change = True

        # If available it has changed
        if attribute is 'UNREACH':
            self._available = bool(value)
            have_change = True

        # If it has changed data point, update HA
        if have_change:
            _LOGGER.debug("%s update_ha_state after '%s'", self._name,
                          attribute)
            self.schedule_update_ha_state()

    def _subscribe_homematic_events(self):
        """Subscribe all required events to handle job."""
        channels_to_sub = {}

        # Push data to channels_to_sub from hmdevice metadata
        for metadata in (self._hmdevice.SENSORNODE, self._hmdevice.BINARYNODE,
                         self._hmdevice.ATTRIBUTENODE,
                         self._hmdevice.WRITENODE, self._hmdevice.EVENTNODE,
                         self._hmdevice.ACTIONNODE):
            for node, channels in list(metadata.items()):
                # Data is needed for this instance
                if node in self._data:
                    # chan is current channel
                    if len(channels) == 1:
                        channel = channels[0]
                    else:
                        channel = self._channel

                    # Prepare for subscription
                    try:
                        if int(channel) >= 0:
                            channels_to_sub.update({int(channel): True})
                    except (ValueError, TypeError):
                        _LOGGER.error("Invalid channel in metadata from %s",
                                      self._name)

        # Set callbacks
        for channel in channels_to_sub:
            _LOGGER.debug("Subscribe channel %s from %s",
                          str(channel), self._name)
            self._hmdevice.setEventCallback(callback=self._hm_event_callback,
                                            bequeath=False,
                                            channel=channel)

    def _load_data_from_hm(self):
        """Load first value from pyhomematic."""
        if not self._connected:
            return False

        # Read data from pyhomematic
        for metadata, funct in (
                (self._hmdevice.ATTRIBUTENODE,
                 self._hmdevice.getAttributeData),
                (self._hmdevice.WRITENODE, self._hmdevice.getWriteData),
                (self._hmdevice.SENSORNODE, self._hmdevice.getSensorData),
                (self._hmdevice.BINARYNODE, self._hmdevice.getBinaryData)):
            for node in metadata:
                if node in self._data:
                    self._data[node] = funct(name=node, channel=self._channel)

        return True

    def _hm_set_state(self, value):
        """Set data to main datapoint."""
        if self._state in self._data:
            self._data[self._state] = value

    def _hm_get_state(self):
        """Get data from main datapoint."""
        if self._state in self._data:
            return self._data[self._state]
        return None

    def _init_data(self):
        """Generate a data dict (self._data) from the Homematic metadata."""
        # Add all attributes to data dict
        for data_note in self._hmdevice.ATTRIBUTENODE:
            self._data.update({data_note: STATE_UNKNOWN})

        # init device specified data
        self._init_data_struct()

    def _init_data_struct(self):
        """Generate a data dict from the Homematic device metadata."""
        raise NotImplementedError

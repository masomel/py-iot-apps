"""
Support for Hue lights.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.hue/
"""
import json
import logging
import os
import random
import socket
from datetime import timedelta
from urllib.parse import urlparse

import voluptuous as vol

import homeassistant.util as util
import homeassistant.util.color as color_util
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_COLOR_TEMP, ATTR_EFFECT, ATTR_FLASH, ATTR_RGB_COLOR,
    ATTR_TRANSITION, ATTR_XY_COLOR, EFFECT_COLORLOOP, EFFECT_RANDOM,
    FLASH_LONG, FLASH_SHORT, SUPPORT_BRIGHTNESS, SUPPORT_COLOR_TEMP,
    SUPPORT_EFFECT, SUPPORT_FLASH, SUPPORT_RGB_COLOR, SUPPORT_TRANSITION,
    SUPPORT_XY_COLOR, Light, PLATFORM_SCHEMA)
from homeassistant.config import load_yaml_config_file
from homeassistant.const import (CONF_FILENAME, CONF_HOST, DEVICE_DEFAULT_NAME)
from homeassistant.loader import get_component
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['phue==0.9']

# Track previously setup bridges
_CONFIGURED_BRIDGES = {}
# Map ip to request id for configuring
_CONFIGURING = {}
_LOGGER = logging.getLogger(__name__)

CONF_ALLOW_UNREACHABLE = 'allow_unreachable'

DEFAULT_ALLOW_UNREACHABLE = False
DOMAIN = "light"
SERVICE_HUE_SCENE = "hue_activate_scene"

MIN_TIME_BETWEEN_SCANS = timedelta(seconds=10)
MIN_TIME_BETWEEN_FORCED_SCANS = timedelta(milliseconds=100)

PHUE_CONFIG_FILE = 'phue.conf'

SUPPORT_HUE = (SUPPORT_BRIGHTNESS | SUPPORT_COLOR_TEMP | SUPPORT_EFFECT |
               SUPPORT_FLASH | SUPPORT_RGB_COLOR | SUPPORT_TRANSITION |
               SUPPORT_XY_COLOR)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_ALLOW_UNREACHABLE): cv.boolean,
    vol.Optional(CONF_FILENAME): cv.string,
})

ATTR_GROUP_NAME = "group_name"
ATTR_SCENE_NAME = "scene_name"
SCENE_SCHEMA = vol.Schema({
    vol.Required(ATTR_GROUP_NAME): cv.string,
    vol.Required(ATTR_SCENE_NAME): cv.string,
})


def _find_host_from_config(hass, filename=PHUE_CONFIG_FILE):
    """Attempt to detect host based on existing configuration."""
    path = hass.config.path(filename)

    if not os.path.isfile(path):
        return None

    try:
        with open(path) as inp:
            return next(json.loads(''.join(inp)).keys().__iter__())
    except (ValueError, AttributeError, StopIteration):
        # ValueError if can't parse as JSON
        # AttributeError if JSON value is not a dict
        # StopIteration if no keys
        return None


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Hue lights."""
    # Default needed in case of discovery
    filename = config.get(CONF_FILENAME, PHUE_CONFIG_FILE)
    allow_unreachable = config.get(CONF_ALLOW_UNREACHABLE,
                                   DEFAULT_ALLOW_UNREACHABLE)

    if discovery_info is not None:
        host = urlparse(discovery_info[1]).hostname

        if "HASS Bridge" in discovery_info[0]:
            _LOGGER.info('Emulated hue found, will not add')
            return False
    else:
        host = config.get(CONF_HOST, None)

        if host is None:
            host = _find_host_from_config(hass, filename)

        if host is None:
            _LOGGER.error('No host found in configuration')
            return False

    # Only act if we are not already configuring this host
    if host in _CONFIGURING or \
            socket.gethostbyname(host) in _CONFIGURED_BRIDGES:
        return

    setup_bridge(host, hass, add_devices, filename, allow_unreachable)


def setup_bridge(host, hass, add_devices, filename, allow_unreachable):
    """Setup a phue bridge based on host parameter."""
    import phue

    try:
        bridge = phue.Bridge(
            host,
            config_file_path=hass.config.path(filename))
    except ConnectionRefusedError:  # Wrong host was given
        _LOGGER.error("Error connecting to the Hue bridge at %s", host)

        return

    except phue.PhueRegistrationException:
        _LOGGER.warning("Connected to Hue at %s but not registered.", host)

        request_configuration(host, hass, add_devices, filename,
                              allow_unreachable)

        return

    # If we came here and configuring this host, mark as done
    if host in _CONFIGURING:
        request_id = _CONFIGURING.pop(host)

        configurator = get_component('configurator')

        configurator.request_done(request_id)

    lights = {}
    lightgroups = {}
    skip_groups = False

    @util.Throttle(MIN_TIME_BETWEEN_SCANS, MIN_TIME_BETWEEN_FORCED_SCANS)
    def update_lights():
        """Update the Hue light objects with latest info from the bridge."""
        nonlocal skip_groups

        try:
            api = bridge.get_api()
        except socket.error:
            # socket.error when we cannot reach Hue
            _LOGGER.exception("Cannot reach the bridge")
            return

        api_lights = api.get('lights')

        if not isinstance(api_lights, dict):
            _LOGGER.error("Got unexpected result from Hue API")
            return

        if skip_groups:
            api_groups = {}
        else:
            api_groups = api.get('groups')

        if not isinstance(api_groups, dict):
            _LOGGER.error("Got unexpected result from Hue API")
            return

        new_lights = []

        api_name = api.get('config').get('name')
        if api_name in ('RaspBee-GW', 'deCONZ-GW'):
            bridge_type = 'deconz'
        else:
            bridge_type = 'hue'

        for light_id, info in api_lights.items():
            if light_id not in lights:
                lights[light_id] = HueLight(int(light_id), info,
                                            bridge, update_lights,
                                            bridge_type, allow_unreachable)
                new_lights.append(lights[light_id])
            else:
                lights[light_id].info = info
                lights[light_id].schedule_update_ha_state()

        for lightgroup_id, info in api_groups.items():
            if 'state' not in info:
                _LOGGER.warning('Group info does not contain state. '
                                'Please update your hub.')
                skip_groups = True
                break

            if lightgroup_id not in lightgroups:
                lightgroups[lightgroup_id] = HueLight(
                    int(lightgroup_id), info, bridge, update_lights,
                    bridge_type, allow_unreachable, True)
                new_lights.append(lightgroups[lightgroup_id])
            else:
                lightgroups[lightgroup_id].info = info
                lightgroups[lightgroup_id].schedule_update_ha_state()

        if new_lights:
            add_devices(new_lights)

    _CONFIGURED_BRIDGES[socket.gethostbyname(host)] = True

    # create a service for calling run_scene directly on the bridge,
    # used to simplify automation rules.
    def hue_activate_scene(call):
        """Service to call directly directly into bridge to set scenes."""
        group_name = call.data[ATTR_GROUP_NAME]
        scene_name = call.data[ATTR_SCENE_NAME]
        bridge.run_scene(group_name, scene_name)

    descriptions = load_yaml_config_file(
        os.path.join(os.path.dirname(__file__), 'services.yaml'))
    hass.services.register(DOMAIN, SERVICE_HUE_SCENE, hue_activate_scene,
                           descriptions.get(SERVICE_HUE_SCENE),
                           schema=SCENE_SCHEMA)

    update_lights()


def request_configuration(host, hass, add_devices, filename,
                          allow_unreachable):
    """Request configuration steps from the user."""
    configurator = get_component('configurator')

    # We got an error if this method is called while we are configuring
    if host in _CONFIGURING:
        configurator.notify_errors(
            _CONFIGURING[host], "Failed to register, please try again.")

        return

    # pylint: disable=unused-argument
    def hue_configuration_callback(data):
        """The actions to do when our configuration callback is called."""
        setup_bridge(host, hass, add_devices, filename, allow_unreachable)

    _CONFIGURING[host] = configurator.request_config(
        hass, "Philips Hue", hue_configuration_callback,
        description=("Press the button on the bridge to register Philips Hue "
                     "with Home Assistant."),
        entity_picture="/static/images/logo_philips_hue.png",
        description_image="/static/images/config_philips_hue.jpg",
        submit_caption="I have pressed the button"
    )


class HueLight(Light):
    """Representation of a Hue light."""

    def __init__(self, light_id, info, bridge, update_lights,
                 bridge_type, allow_unreachable, is_group=False):
        """Initialize the light."""
        self.light_id = light_id
        self.info = info
        self.bridge = bridge
        self.update_lights = update_lights
        self.bridge_type = bridge_type
        self.allow_unreachable = allow_unreachable
        self.is_group = is_group

        if is_group:
            self._command_func = self.bridge.set_group
        else:
            self._command_func = self.bridge.set_light

    @property
    def unique_id(self):
        """Return the ID of this Hue light."""
        return "{}.{}".format(
            self.__class__, self.info.get('uniqueid', self.name))

    @property
    def name(self):
        """Return the name of the Hue light."""
        return self.info.get('name', DEVICE_DEFAULT_NAME)

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        if self.is_group:
            return self.info['action'].get('bri')
        else:
            return self.info['state'].get('bri')

    @property
    def xy_color(self):
        """Return the XY color value."""
        if self.is_group:
            return self.info['action'].get('xy')
        else:
            return self.info['state'].get('xy')

    @property
    def color_temp(self):
        """Return the CT color value."""
        if self.is_group:
            return self.info['action'].get('ct')
        else:
            return self.info['state'].get('ct')

    @property
    def is_on(self):
        """Return true if device is on."""
        if self.is_group:
            return self.info['state']['any_on']
        else:
            if self.allow_unreachable:
                return self.info['state']['on']
            else:
                return self.info['state']['reachable'] and \
                    self.info['state']['on']

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_HUE

    def turn_on(self, **kwargs):
        """Turn the specified or all lights on."""
        command = {'on': True}

        if ATTR_TRANSITION in kwargs:
            command['transitiontime'] = kwargs[ATTR_TRANSITION] * 10

        if ATTR_XY_COLOR in kwargs:
            command['xy'] = kwargs[ATTR_XY_COLOR]
        elif ATTR_RGB_COLOR in kwargs:
            xyb = color_util.color_RGB_to_xy(
                *(int(val) for val in kwargs[ATTR_RGB_COLOR]))
            command['xy'] = xyb[0], xyb[1]
            command['bri'] = xyb[2]

        if ATTR_BRIGHTNESS in kwargs:
            command['bri'] = kwargs[ATTR_BRIGHTNESS]

        if ATTR_COLOR_TEMP in kwargs:
            command['ct'] = kwargs[ATTR_COLOR_TEMP]

        flash = kwargs.get(ATTR_FLASH)

        if flash == FLASH_LONG:
            command['alert'] = 'lselect'
            del command['on']
        elif flash == FLASH_SHORT:
            command['alert'] = 'select'
            del command['on']
        elif self.bridge_type == 'hue':
            command['alert'] = 'none'

        effect = kwargs.get(ATTR_EFFECT)

        if effect == EFFECT_COLORLOOP:
            command['effect'] = 'colorloop'
        elif effect == EFFECT_RANDOM:
            command['hue'] = random.randrange(0, 65535)
            command['sat'] = random.randrange(150, 254)
        elif self.bridge_type == 'hue':
            command['effect'] = 'none'

        self._command_func(self.light_id, command)

    def turn_off(self, **kwargs):
        """Turn the specified or all lights off."""
        command = {'on': False}

        if ATTR_TRANSITION in kwargs:
            # Transition time is in 1/10th seconds and cannot exceed
            # 900 seconds.
            command['transitiontime'] = min(9000, kwargs[ATTR_TRANSITION] * 10)

        flash = kwargs.get(ATTR_FLASH)

        if flash == FLASH_LONG:
            command['alert'] = 'lselect'
            del command['on']
        elif flash == FLASH_SHORT:
            command['alert'] = 'select'
            del command['on']
        elif self.bridge_type == 'hue':
            command['alert'] = 'none'

        self._command_func(self.light_id, command)

    def update(self):
        """Synchronize state with bridge."""
        self.update_lights(no_throttle=True)

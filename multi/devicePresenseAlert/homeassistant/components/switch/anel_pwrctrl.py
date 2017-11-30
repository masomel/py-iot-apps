"""
Support for ANEL PwrCtrl switches.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.pwrctrl/
"""
import logging
import socket
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.switch import (SwitchDevice, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_HOST, CONF_PASSWORD, CONF_USERNAME)
from homeassistant.util import Throttle

REQUIREMENTS = ['https://github.com/mweinelt/anel-pwrctrl/archive/'
                'ed26e8830e28a2bfa4260a9002db23ce3e7e63d7.zip'
                '#anel_pwrctrl==0.0.1']

_LOGGER = logging.getLogger(__name__)

CONF_PORT_RECV = "port_recv"
CONF_PORT_SEND = "port_send"

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=5)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PORT_RECV): cv.port,
    vol.Required(CONF_PORT_SEND): cv.port,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_HOST): cv.string,
})


# pylint: disable=unused-variable
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup PwrCtrl devices/switches."""
    host = config.get(CONF_HOST, None)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    port_recv = config.get(CONF_PORT_RECV)
    port_send = config.get(CONF_PORT_SEND)

    from anel_pwrctrl import DeviceMaster

    try:
        master = DeviceMaster(
            username=username, password=password, read_port=port_send,
            write_port=port_recv)
        master.query(ip_addr=host)
    except socket.error as ex:
        _LOGGER.error("Unable to discover PwrCtrl device: %s", str(ex))
        return False

    devices = []
    for device in master.devices.values():
        parent_device = PwrCtrlDevice(device)
        devices.extend(
            PwrCtrlSwitch(switch, parent_device)
            for switch in device.switches.values()
        )

    add_devices(devices)


class PwrCtrlSwitch(SwitchDevice):
    """Representation of a PwrCtrl switch."""

    def __init__(self, port, parent_device):
        """Initialize the PwrCtrl switch."""
        self._port = port
        self._parent_device = parent_device

    @property
    def should_poll(self):
        """Polling is needed."""
        return True

    @property
    def unique_id(self):
        """Return the unique ID of the device."""
        return '{device}-{switch_idx}'.format(
            device=self._port.device.host,
            switch_idx=self._port.get_index()
        )

    @property
    def name(self):
        """Return the name of the device."""
        return self._port.label

    @property
    def is_on(self):
        """Return true if the device is on."""
        return self._port.get_state()

    def update(self):
        """Trigger update for all switches on the parent device."""
        self._parent_device.update()

    def turn_on(self):
        """Turn the switch on."""
        self._port.on()

    def turn_off(self):
        """Turn the switch off."""
        self._port.off()


class PwrCtrlDevice(object):
    """Device representation for per device throttling."""

    def __init__(self, device):
        """Initialize the PwrCtrl device."""
        self._device = device

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update the device and all its switches."""
        self._device.update()

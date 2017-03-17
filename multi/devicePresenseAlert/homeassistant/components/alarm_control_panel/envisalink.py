"""
Support for Envisalink-based alarm control panels (Honeywell/DSC).

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/alarm_control_panel.envisalink/
"""
from os import path
import logging
import voluptuous as vol

import homeassistant.components.alarm_control_panel as alarm
import homeassistant.helpers.config_validation as cv
from homeassistant.config import load_yaml_config_file
from homeassistant.components.envisalink import (
    EVL_CONTROLLER, EnvisalinkDevice, PARTITION_SCHEMA, CONF_CODE, CONF_PANIC,
    CONF_PARTITIONNAME, SIGNAL_PARTITION_UPDATE, SIGNAL_KEYPAD_UPDATE)
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY, STATE_ALARM_ARMED_HOME, STATE_ALARM_DISARMED,
    STATE_UNKNOWN, STATE_ALARM_TRIGGERED, STATE_ALARM_PENDING, ATTR_ENTITY_ID)

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['envisalink']

DEVICES = []

SERVICE_ALARM_KEYPRESS = 'envisalink_alarm_keypress'
ATTR_KEYPRESS = 'keypress'
ALARM_KEYPRESS_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_KEYPRESS): cv.string
})


def alarm_keypress_handler(service):
    """Map services to methods on Alarm."""
    entity_ids = service.data.get(ATTR_ENTITY_ID)
    keypress = service.data.get(ATTR_KEYPRESS)

    _target_devices = [device for device in DEVICES
                       if device.entity_id in entity_ids]

    for device in _target_devices:
        EnvisalinkAlarm.alarm_keypress(device, keypress)


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Perform the setup for Envisalink alarm panels."""
    _configured_partitions = discovery_info['partitions']
    _code = discovery_info[CONF_CODE]
    _panic_type = discovery_info[CONF_PANIC]
    for part_num in _configured_partitions:
        _device_config_data = PARTITION_SCHEMA(
            _configured_partitions[part_num])
        _device = EnvisalinkAlarm(
            part_num,
            _device_config_data[CONF_PARTITIONNAME],
            _code,
            _panic_type,
            EVL_CONTROLLER.alarm_state['partition'][part_num],
            EVL_CONTROLLER)
        DEVICES.append(_device)

    add_devices(DEVICES)

    # Register Envisalink specific services
    descriptions = load_yaml_config_file(
        path.join(path.dirname(__file__), 'services.yaml'))

    hass.services.register(alarm.DOMAIN, SERVICE_ALARM_KEYPRESS,
                           alarm_keypress_handler,
                           descriptions.get(SERVICE_ALARM_KEYPRESS),
                           schema=ALARM_KEYPRESS_SCHEMA)
    return True


class EnvisalinkAlarm(EnvisalinkDevice, alarm.AlarmControlPanel):
    """Representation of an Envisalink-based alarm panel."""

    def __init__(self, partition_number, alarm_name, code, panic_type, info,
                 controller):
        """Initialize the alarm panel."""
        from pydispatch import dispatcher
        self._partition_number = partition_number
        self._code = code
        self._panic_type = panic_type
        _LOGGER.debug("Setting up alarm: %s", alarm_name)
        EnvisalinkDevice.__init__(self, alarm_name, info, controller)
        dispatcher.connect(
            self._update_callback, signal=SIGNAL_PARTITION_UPDATE,
            sender=dispatcher.Any)
        dispatcher.connect(
            self._update_callback, signal=SIGNAL_KEYPAD_UPDATE,
            sender=dispatcher.Any)

    def _update_callback(self, partition):
        """Update HA state, if needed."""
        if partition is None or int(partition) == self._partition_number:
            self.hass.async_add_job(self.async_update_ha_state())

    @property
    def code_format(self):
        """Regex for code format or None if no code is required."""
        if self._code:
            return None
        else:
            return '^\\d{4,6}$'

    @property
    def state(self):
        """Return the state of the device."""
        state = STATE_UNKNOWN

        if self._info['status']['alarm']:
            state = STATE_ALARM_TRIGGERED
        elif self._info['status']['armed_away']:
            state = STATE_ALARM_ARMED_AWAY
        elif self._info['status']['armed_stay']:
            state = STATE_ALARM_ARMED_HOME
        elif self._info['status']['exit_delay']:
            state = STATE_ALARM_PENDING
        elif self._info['status']['entry_delay']:
            state = STATE_ALARM_PENDING
        elif self._info['status']['alpha']:
            state = STATE_ALARM_DISARMED
        return state

    def alarm_disarm(self, code=None):
        """Send disarm command."""
        if code:
            EVL_CONTROLLER.disarm_partition(str(code),
                                            self._partition_number)
        else:
            EVL_CONTROLLER.disarm_partition(str(self._code),
                                            self._partition_number)

    def alarm_arm_home(self, code=None):
        """Send arm home command."""
        if code:
            EVL_CONTROLLER.arm_stay_partition(str(code),
                                              self._partition_number)
        else:
            EVL_CONTROLLER.arm_stay_partition(str(self._code),
                                              self._partition_number)

    def alarm_arm_away(self, code=None):
        """Send arm away command."""
        if code:
            EVL_CONTROLLER.arm_away_partition(str(code),
                                              self._partition_number)
        else:
            EVL_CONTROLLER.arm_away_partition(str(self._code),
                                              self._partition_number)

    def alarm_trigger(self, code=None):
        """Alarm trigger command. Will be used to trigger a panic alarm."""
        EVL_CONTROLLER.panic_alarm(self._panic_type)

    def alarm_keypress(self, keypress=None):
        """Send custom keypress."""
        if keypress:
            EVL_CONTROLLER.keypresses_to_partition(self._partition_number,
                                                   keypress)

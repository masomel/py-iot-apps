"""
Component to interface with various switches that can be controlled remotely.

For more details about this component, please refer to the documentation
at https://home-assistant.io/components/switch/
"""
import asyncio
from datetime import timedelta
import logging
import os

import voluptuous as vol

from homeassistant.config import load_yaml_config_file
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA  # noqa
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    STATE_ON, SERVICE_TURN_ON, SERVICE_TURN_OFF, SERVICE_TOGGLE,
    ATTR_ENTITY_ID)
from homeassistant.components import group

DOMAIN = 'switch'
SCAN_INTERVAL = timedelta(seconds=30)

GROUP_NAME_ALL_SWITCHES = 'all switches'
ENTITY_ID_ALL_SWITCHES = group.ENTITY_ID_FORMAT.format('all_switches')

ENTITY_ID_FORMAT = DOMAIN + '.{}'

ATTR_TODAY_MWH = "today_mwh"
ATTR_CURRENT_POWER_MWH = "current_power_mwh"

MIN_TIME_BETWEEN_SCANS = timedelta(seconds=10)

PROP_TO_ATTR = {
    'current_power_mwh': ATTR_CURRENT_POWER_MWH,
    'today_power_mw': ATTR_TODAY_MWH,
}

SWITCH_SERVICE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
})

_LOGGER = logging.getLogger(__name__)


def is_on(hass, entity_id=None):
    """Return if the switch is on based on the statemachine."""
    entity_id = entity_id or ENTITY_ID_ALL_SWITCHES
    return hass.states.is_state(entity_id, STATE_ON)


def turn_on(hass, entity_id=None):
    """Turn all or specified switch on."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else None
    hass.services.call(DOMAIN, SERVICE_TURN_ON, data)


def turn_off(hass, entity_id=None):
    """Turn all or specified switch off."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else None
    hass.services.call(DOMAIN, SERVICE_TURN_OFF, data)


def toggle(hass, entity_id=None):
    """Toggle all or specified switch."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else None
    hass.services.call(DOMAIN, SERVICE_TOGGLE, data)


@asyncio.coroutine
def async_setup(hass, config):
    """Track states and offer events for switches."""
    component = EntityComponent(
        _LOGGER, DOMAIN, hass, SCAN_INTERVAL, GROUP_NAME_ALL_SWITCHES)
    yield from component.async_setup(config)

    @asyncio.coroutine
    def async_handle_switch_service(service):
        """Handle calls to the switch services."""
        target_switches = component.async_extract_from_service(service)

        for switch in target_switches:
            if service.service == SERVICE_TURN_ON:
                yield from switch.async_turn_on()
            elif service.service == SERVICE_TOGGLE:
                yield from switch.async_toggle()
            else:
                yield from switch.async_turn_off()

        update_tasks = []
        for switch in target_switches:
            if not switch.should_poll:
                continue

            update_coro = hass.loop.create_task(
                switch.async_update_ha_state(True))
            if hasattr(switch, 'async_update'):
                update_tasks.append(update_coro)
            else:
                yield from update_coro

        if update_tasks:
            yield from asyncio.wait(update_tasks, loop=hass.loop)

    descriptions = yield from hass.loop.run_in_executor(
        None, load_yaml_config_file, os.path.join(
            os.path.dirname(__file__), 'services.yaml'))

    hass.services.async_register(
        DOMAIN, SERVICE_TURN_OFF, async_handle_switch_service,
        descriptions.get(SERVICE_TURN_OFF), schema=SWITCH_SERVICE_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_TURN_ON, async_handle_switch_service,
        descriptions.get(SERVICE_TURN_ON), schema=SWITCH_SERVICE_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_TOGGLE, async_handle_switch_service,
        descriptions.get(SERVICE_TOGGLE), schema=SWITCH_SERVICE_SCHEMA)

    return True


class SwitchDevice(ToggleEntity):
    """Representation of a switch."""

    # pylint: disable=no-self-use
    @property
    def current_power_mwh(self):
        """Return the current power usage in mWh."""
        return None

    @property
    def today_power_mw(self):
        """Return the today total power usage in mW."""
        return None

    @property
    def is_standby(self):
        """Return true if device is in standby."""
        return None

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data = {}

        for prop, attr in list(PROP_TO_ATTR.items()):
            value = getattr(self, prop)
            if value:
                data[attr] = value

        return data

"""
Component to keep track of user controlled booleans for within automation.

For more details about this component, please refer to the documentation
at https://home-assistant.io/components/input_boolean/
"""
import asyncio
import logging

import voluptuous as vol

from homeassistant.const import (
    ATTR_ENTITY_ID, CONF_ICON, CONF_NAME, SERVICE_TURN_OFF, SERVICE_TURN_ON,
    SERVICE_TOGGLE, STATE_ON)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.entity_component import EntityComponent

DOMAIN = 'input_boolean'

ENTITY_ID_FORMAT = DOMAIN + '.{}'

_LOGGER = logging.getLogger(__name__)

CONF_INITIAL = 'initial'
DEFAULT_INITIAL = False

SERVICE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
})

DEFAULT_CONFIG = {CONF_INITIAL: DEFAULT_INITIAL}

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        cv.slug: vol.Any({
            vol.Optional(CONF_NAME): cv.string,
            vol.Optional(CONF_INITIAL, default=DEFAULT_INITIAL): cv.boolean,
            vol.Optional(CONF_ICON): cv.icon,
        }, None)
    })
}, extra=vol.ALLOW_EXTRA)


def is_on(hass, entity_id):
    """Test if input_boolean is True."""
    return hass.states.is_state(entity_id, STATE_ON)


def turn_on(hass, entity_id):
    """Set input_boolean to True."""
    hass.services.call(DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: entity_id})


def turn_off(hass, entity_id):
    """Set input_boolean to False."""
    hass.services.call(DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id})


def toggle(hass, entity_id):
    """Set input_boolean to False."""
    hass.services.call(DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: entity_id})


@asyncio.coroutine
def async_setup(hass, config):
    """Set up input boolean."""
    component = EntityComponent(_LOGGER, DOMAIN, hass)

    entities = []

    for object_id, cfg in config[DOMAIN].items():
        if not cfg:
            cfg = DEFAULT_CONFIG

        name = cfg.get(CONF_NAME)
        state = cfg.get(CONF_INITIAL)
        icon = cfg.get(CONF_ICON)

        entities.append(InputBoolean(object_id, name, state, icon))

    if not entities:
        return False

    @asyncio.coroutine
    def async_handler_service(service):
        """Handle a calls to the input boolean services."""
        target_inputs = component.async_extract_from_service(service)

        if service.service == SERVICE_TURN_ON:
            attr = 'async_turn_on'
        elif service.service == SERVICE_TURN_OFF:
            attr = 'async_turn_off'
        else:
            attr = 'async_toggle'

        tasks = [getattr(input_b, attr)() for input_b in target_inputs]
        if tasks:
            yield from asyncio.wait(tasks, loop=hass.loop)

    hass.services.async_register(
        DOMAIN, SERVICE_TURN_OFF, async_handler_service, schema=SERVICE_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_TURN_ON, async_handler_service, schema=SERVICE_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_TOGGLE, async_handler_service, schema=SERVICE_SCHEMA)

    yield from component.async_add_entities(entities)
    return True


class InputBoolean(ToggleEntity):
    """Representation of a boolean input."""

    def __init__(self, object_id, name, state, icon):
        """Initialize a boolean input."""
        self.entity_id = ENTITY_ID_FORMAT.format(object_id)
        self._name = name
        self._state = state
        self._icon = icon

    @property
    def should_poll(self):
        """If entity should be polled."""
        return False

    @property
    def name(self):
        """Return name of the boolean input."""
        return self._name

    @property
    def icon(self):
        """Returh the icon to be used for this entity."""
        return self._icon

    @property
    def is_on(self):
        """Return true if entity is on."""
        return self._state

    @asyncio.coroutine
    def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self._state = True
        yield from self.async_update_ha_state()

    @asyncio.coroutine
    def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self._state = False
        yield from self.async_update_ha_state()

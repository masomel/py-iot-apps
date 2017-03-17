"""
Allow to setup simple automation rules via the config file.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/automation/
"""
import asyncio
from functools import partial
import logging
import os

import voluptuous as vol

from homeassistant.bootstrap import async_prepare_setup_platform
from homeassistant import config as conf_util
from homeassistant.const import (
    ATTR_ENTITY_ID, CONF_PLATFORM, STATE_ON, SERVICE_TURN_ON, SERVICE_TURN_OFF,
    SERVICE_TOGGLE)
from homeassistant.components import logbook
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import extract_domain_configs, script, condition
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.loader import get_platform
from homeassistant.util.dt import utcnow
import homeassistant.helpers.config_validation as cv

DOMAIN = 'automation'
ENTITY_ID_FORMAT = DOMAIN + '.{}'

DEPENDENCIES = ['group']

GROUP_NAME_ALL_AUTOMATIONS = 'all automations'

CONF_ALIAS = 'alias'
CONF_HIDE_ENTITY = 'hide_entity'

CONF_CONDITION = 'condition'
CONF_ACTION = 'action'
CONF_TRIGGER = 'trigger'
CONF_CONDITION_TYPE = 'condition_type'
CONF_INITIAL_STATE = 'initial_state'

CONDITION_USE_TRIGGER_VALUES = 'use_trigger_values'
CONDITION_TYPE_AND = 'and'
CONDITION_TYPE_OR = 'or'

DEFAULT_CONDITION_TYPE = CONDITION_TYPE_AND
DEFAULT_HIDE_ENTITY = False
DEFAULT_INITIAL_STATE = True

ATTR_LAST_TRIGGERED = 'last_triggered'
ATTR_VARIABLES = 'variables'
SERVICE_TRIGGER = 'trigger'
SERVICE_RELOAD = 'reload'

_LOGGER = logging.getLogger(__name__)


def _platform_validator(config):
    """Validate it is a valid  platform."""
    platform = get_platform(DOMAIN, config[CONF_PLATFORM])

    if not hasattr(platform, 'TRIGGER_SCHEMA'):
        return config

    return getattr(platform, 'TRIGGER_SCHEMA')(config)


_TRIGGER_SCHEMA = vol.All(
    cv.ensure_list,
    [
        vol.All(
            vol.Schema({
                vol.Required(CONF_PLATFORM): cv.platform_validator(DOMAIN)
            }, extra=vol.ALLOW_EXTRA),
            _platform_validator
        ),
    ]
)

_CONDITION_SCHEMA = vol.All(cv.ensure_list, [cv.CONDITION_SCHEMA])

PLATFORM_SCHEMA = vol.Schema({
    CONF_ALIAS: cv.string,
    vol.Optional(CONF_INITIAL_STATE,
                 default=DEFAULT_INITIAL_STATE): cv.boolean,
    vol.Optional(CONF_HIDE_ENTITY, default=DEFAULT_HIDE_ENTITY): cv.boolean,
    vol.Required(CONF_TRIGGER): _TRIGGER_SCHEMA,
    vol.Optional(CONF_CONDITION): _CONDITION_SCHEMA,
    vol.Required(CONF_ACTION): cv.SCRIPT_SCHEMA,
})

SERVICE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
})

TRIGGER_SERVICE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Optional(ATTR_VARIABLES, default={}): dict,
})

RELOAD_SERVICE_SCHEMA = vol.Schema({})


def is_on(hass, entity_id=None):
    """
    Return true if specified automation entity_id is on.

    Check all automation if no entity_id specified.
    """
    entity_ids = [entity_id] if entity_id else hass.states.entity_ids(DOMAIN)
    return any(hass.states.is_state(entity_id, STATE_ON)
               for entity_id in entity_ids)


def turn_on(hass, entity_id=None):
    """Turn on specified automation or all."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    hass.services.call(DOMAIN, SERVICE_TURN_ON, data)


def turn_off(hass, entity_id=None):
    """Turn off specified automation or all."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    hass.services.call(DOMAIN, SERVICE_TURN_OFF, data)


def toggle(hass, entity_id=None):
    """Toggle specified automation or all."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    hass.services.call(DOMAIN, SERVICE_TOGGLE, data)


def trigger(hass, entity_id=None):
    """Trigger specified automation or all."""
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    hass.services.call(DOMAIN, SERVICE_TRIGGER, data)


def reload(hass):
    """Reload the automation from config."""
    hass.services.call(DOMAIN, SERVICE_RELOAD)


@asyncio.coroutine
def async_setup(hass, config):
    """Setup the automation."""
    component = EntityComponent(_LOGGER, DOMAIN, hass,
                                group_name=GROUP_NAME_ALL_AUTOMATIONS)

    success = yield from _async_process_config(hass, config, component)

    if not success:
        return False

    descriptions = yield from hass.loop.run_in_executor(
        None, conf_util.load_yaml_config_file, os.path.join(
            os.path.dirname(__file__), 'services.yaml')
    )

    @asyncio.coroutine
    def trigger_service_handler(service_call):
        """Handle automation triggers."""
        tasks = []
        for entity in component.async_extract_from_service(service_call):
            tasks.append(entity.async_trigger(
                service_call.data.get(ATTR_VARIABLES), True))

        if tasks:
            yield from asyncio.wait(tasks, loop=hass.loop)

    @asyncio.coroutine
    def turn_onoff_service_handler(service_call):
        """Handle automation turn on/off service calls."""
        tasks = []
        method = 'async_{}'.format(service_call.service)
        for entity in component.async_extract_from_service(service_call):
            tasks.append(getattr(entity, method)())

        if tasks:
            yield from asyncio.wait(tasks, loop=hass.loop)

    @asyncio.coroutine
    def toggle_service_handler(service_call):
        """Handle automation toggle service calls."""
        tasks = []
        for entity in component.async_extract_from_service(service_call):
            if entity.is_on:
                tasks.append(entity.async_turn_off())
            else:
                tasks.append(entity.async_turn_on())

        if tasks:
            yield from asyncio.wait(tasks, loop=hass.loop)

    @asyncio.coroutine
    def reload_service_handler(service_call):
        """Remove all automations and load new ones from config."""
        conf = yield from component.async_prepare_reload()
        if conf is None:
            return
        yield from _async_process_config(hass, conf, component)

    hass.services.async_register(
        DOMAIN, SERVICE_TRIGGER, trigger_service_handler,
        descriptions.get(SERVICE_TRIGGER), schema=TRIGGER_SERVICE_SCHEMA)

    hass.services.async_register(
        DOMAIN, SERVICE_RELOAD, reload_service_handler,
        descriptions.get(SERVICE_RELOAD), schema=RELOAD_SERVICE_SCHEMA)

    hass.services.async_register(
        DOMAIN, SERVICE_TOGGLE, toggle_service_handler,
        descriptions.get(SERVICE_TOGGLE), schema=SERVICE_SCHEMA)

    for service in (SERVICE_TURN_ON, SERVICE_TURN_OFF):
        hass.services.async_register(
            DOMAIN, service, turn_onoff_service_handler,
            descriptions.get(service), schema=SERVICE_SCHEMA)

    return True


class AutomationEntity(ToggleEntity):
    """Entity to show status of entity."""

    def __init__(self, name, async_attach_triggers, cond_func, async_action,
                 hidden):
        """Initialize an automation entity."""
        self._name = name
        self._async_attach_triggers = async_attach_triggers
        self._async_detach_triggers = None
        self._cond_func = cond_func
        self._async_action = async_action
        self._enabled = False
        self._last_triggered = None
        self._hidden = hidden

    @property
    def name(self):
        """Name of the automation."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed for automation entities."""
        return False

    @property
    def state_attributes(self):
        """Return the entity state attributes."""
        return {
            ATTR_LAST_TRIGGERED: self._last_triggered
        }

    @property
    def hidden(self) -> bool:
        """Return True if the automation entity should be hidden from UIs."""
        return self._hidden

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self._enabled

    @asyncio.coroutine
    def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on and update the state."""
        if self._enabled:
            return

        yield from self.async_enable()
        yield from self.async_update_ha_state()

    @asyncio.coroutine
    def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        if not self._enabled:
            return

        self._async_detach_triggers()
        self._async_detach_triggers = None
        self._enabled = False
        yield from self.async_update_ha_state()

    @asyncio.coroutine
    def async_trigger(self, variables, skip_condition=False):
        """Trigger automation.

        This method is a coroutine.
        """
        if skip_condition or self._cond_func(variables):
            yield from self._async_action(self.entity_id, variables)
            self._last_triggered = utcnow()
            yield from self.async_update_ha_state()

    @asyncio.coroutine
    def async_remove(self):
        """Remove automation from HASS."""
        yield from self.async_turn_off()
        yield from super().async_remove()

    @asyncio.coroutine
    def async_enable(self):
        """Enable this automation entity.

        This method is a coroutine.
        """
        if self._enabled:
            return

        self._async_detach_triggers = yield from self._async_attach_triggers(
            self.async_trigger)
        self._enabled = True


@asyncio.coroutine
def _async_process_config(hass, config, component):
    """Process config and add automations.

    This method is a coroutine.
    """
    entities = []
    tasks = []

    for config_key in extract_domain_configs(config, DOMAIN):
        conf = config[config_key]

        for list_no, config_block in enumerate(conf):
            name = config_block.get(CONF_ALIAS) or "{} {}".format(config_key,
                                                                  list_no)

            hidden = config_block[CONF_HIDE_ENTITY]

            action = _async_get_action(hass, config_block.get(CONF_ACTION, {}),
                                       name)

            if CONF_CONDITION in config_block:
                cond_func = _async_process_if(hass, config, config_block)

                if cond_func is None:
                    continue
            else:
                def cond_func(variables):
                    """Condition will always pass."""
                    return True

            async_attach_triggers = partial(
                _async_process_trigger, hass, config,
                config_block.get(CONF_TRIGGER, []), name)
            entity = AutomationEntity(name, async_attach_triggers, cond_func,
                                      action, hidden)
            if config_block[CONF_INITIAL_STATE]:
                tasks.append(entity.async_enable())
            entities.append(entity)

    if tasks:
        yield from asyncio.wait(tasks, loop=hass.loop)
    if entities:
        yield from component.async_add_entities(entities)

    return len(entities) > 0


def _async_get_action(hass, config, name):
    """Return an action based on a configuration."""
    script_obj = script.Script(hass, config, name)

    @asyncio.coroutine
    def action(entity_id, variables):
        """Action to be executed."""
        _LOGGER.info('Executing %s', name)
        logbook.async_log_entry(
            hass, name, 'has been triggered', DOMAIN, entity_id)
        yield from script_obj.async_run(variables)

    return action


def _async_process_if(hass, config, p_config):
    """Process if checks."""
    if_configs = p_config.get(CONF_CONDITION)

    checks = []
    for if_config in if_configs:
        try:
            checks.append(condition.async_from_config(if_config, False))
        except HomeAssistantError as ex:
            _LOGGER.warning('Invalid condition: %s', ex)
            return None

    def if_action(variables=None):
        """AND all conditions."""
        return all(check(hass, variables) for check in checks)

    return if_action


@asyncio.coroutine
def _async_process_trigger(hass, config, trigger_configs, name, action):
    """Setup the triggers.

    This method is a coroutine.
    """
    removes = []

    for conf in trigger_configs:
        platform = yield from async_prepare_setup_platform(
            hass, config, DOMAIN, conf.get(CONF_PLATFORM))

        if platform is None:
            return None

        remove = platform.async_trigger(hass, conf, action)

        if not remove:
            _LOGGER.error("Error setting up trigger %s", name)
            continue

        _LOGGER.info("Initialized trigger %s", name)
        removes.append(remove)

    if not removes:
        return None

    def remove_triggers():
        """Remove attached triggers."""
        for remove in removes:
            remove()

    return remove_triggers

"""
This package contains components that can be plugged into Home Assistant.

Component design guidelines:
- Each component defines a constant DOMAIN that is equal to its filename.
- Each component that tracks states should create state entity names in the
  format "<DOMAIN>.<OBJECT_ID>".
- Each component should publish services only under its own domain.
"""
import asyncio
import itertools as it
import logging

import homeassistant.core as ha
from homeassistant.helpers.service import extract_entity_ids
from homeassistant.loader import get_component
from homeassistant.const import (
    ATTR_ENTITY_ID, SERVICE_TURN_ON, SERVICE_TURN_OFF, SERVICE_TOGGLE)

_LOGGER = logging.getLogger(__name__)

SERVICE_RELOAD_CORE_CONFIG = 'reload_core_config'


def is_on(hass, entity_id=None):
    """Load up the module to call the is_on method.

    If there is no entity id given we will check all.
    """
    if entity_id:
        group = get_component('group')

        entity_ids = group.expand_entity_ids(hass, [entity_id])
    else:
        entity_ids = hass.states.entity_ids()

    for entity_id in entity_ids:
        domain = ha.split_entity_id(entity_id)[0]

        module = get_component(domain)

        try:
            if module.is_on(hass, entity_id):
                return True

        except AttributeError:
            # module is None or method is_on does not exist
            _LOGGER.exception("Failed to call %s.is_on for %s",
                              module, entity_id)

    return False


def turn_on(hass, entity_id=None, **service_data):
    """Turn specified entity on if possible."""
    if entity_id is not None:
        service_data[ATTR_ENTITY_ID] = entity_id

    hass.services.call(ha.DOMAIN, SERVICE_TURN_ON, service_data)


def turn_off(hass, entity_id=None, **service_data):
    """Turn specified entity off."""
    if entity_id is not None:
        service_data[ATTR_ENTITY_ID] = entity_id

    hass.services.call(ha.DOMAIN, SERVICE_TURN_OFF, service_data)


def toggle(hass, entity_id=None, **service_data):
    """Toggle specified entity."""
    if entity_id is not None:
        service_data[ATTR_ENTITY_ID] = entity_id

    hass.services.call(ha.DOMAIN, SERVICE_TOGGLE, service_data)


def reload_core_config(hass):
    """Reload the core config."""
    hass.services.call(ha.DOMAIN, SERVICE_RELOAD_CORE_CONFIG)


@asyncio.coroutine
def async_setup(hass, config):
    """Setup general services related to Home Assistant."""
    @asyncio.coroutine
    def handle_turn_service(service):
        """Method to handle calls to homeassistant.turn_on/off."""
        entity_ids = extract_entity_ids(hass, service)

        # Generic turn on/off method requires entity id
        if not entity_ids:
            _LOGGER.error(
                "homeassistant/%s cannot be called without entity_id",
                service.service)
            return

        # Group entity_ids by domain. groupby requires sorted data.
        by_domain = it.groupby(sorted(entity_ids),
                               lambda item: ha.split_entity_id(item)[0])

        tasks = []

        for domain, ent_ids in by_domain:
            # We want to block for all calls and only return when all calls
            # have been processed. If a service does not exist it causes a 10
            # second delay while we're blocking waiting for a response.
            # But services can be registered on other HA instances that are
            # listening to the bus too. So as a in between solution, we'll
            # block only if the service is defined in the current HA instance.
            blocking = hass.services.has_service(domain, service.service)

            # Create a new dict for this call
            data = dict(service.data)

            # ent_ids is a generator, convert it to a list.
            data[ATTR_ENTITY_ID] = list(ent_ids)

            tasks.append(hass.services.async_call(
                domain, service.service, data, blocking))

        yield from asyncio.wait(tasks, loop=hass.loop)

    hass.services.async_register(
        ha.DOMAIN, SERVICE_TURN_OFF, handle_turn_service)
    hass.services.async_register(
        ha.DOMAIN, SERVICE_TURN_ON, handle_turn_service)
    hass.services.async_register(
        ha.DOMAIN, SERVICE_TOGGLE, handle_turn_service)

    @asyncio.coroutine
    def handle_reload_config(call):
        """Service handler for reloading core config."""
        from homeassistant.exceptions import HomeAssistantError
        from homeassistant import config as conf_util

        try:
            conf = yield from conf_util.async_hass_config_yaml(hass)
        except HomeAssistantError as err:
            _LOGGER.error(err)
            return

        yield from conf_util.async_process_ha_core_config(
            hass, conf.get(ha.DOMAIN) or {})

    hass.services.async_register(
        ha.DOMAIN, SERVICE_RELOAD_CORE_CONFIG, handle_reload_config)

    return True

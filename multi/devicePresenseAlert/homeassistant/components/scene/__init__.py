"""
Allow users to set and activate scenes.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/scene/
"""
import asyncio
import logging
from collections import namedtuple

import voluptuous as vol

from homeassistant.const import (
    ATTR_ENTITY_ID, SERVICE_TURN_ON, CONF_PLATFORM)
from homeassistant.helpers import extract_domain_configs
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent

DOMAIN = 'scene'
DEPENDENCIES = ['group']
STATE = 'scening'

CONF_ENTITIES = "entities"

SCENE_SERVICE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
})

SceneConfig = namedtuple('SceneConfig', ['name', 'states'])


def activate(hass, entity_id=None):
    """Activate a scene."""
    data = {}

    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id

    hass.services.call(DOMAIN, SERVICE_TURN_ON, data)


@asyncio.coroutine
def async_setup(hass, config):
    """Setup scenes."""
    logger = logging.getLogger(__name__)

    # You are not allowed to mutate the original config so make a copy
    config = dict(config)

    for config_key in extract_domain_configs(config, DOMAIN):
        platform_config = config[config_key]
        if not isinstance(platform_config, list):
            platform_config = [platform_config]

        if not any(CONF_PLATFORM in entry for entry in platform_config):
            platform_config = [{'platform': 'homeassistant', 'states': entry}
                               for entry in platform_config]

        config[config_key] = platform_config

    component = EntityComponent(logger, DOMAIN, hass)

    yield from component.async_setup(config)

    @asyncio.coroutine
    def async_handle_scene_service(service):
        """Handle calls to the switch services."""
        target_scenes = component.async_extract_from_service(service)

        tasks = [scene.async_activate() for scene in target_scenes]
        if tasks:
            yield from asyncio.wait(tasks, loop=hass.loop)

    hass.services.async_register(
        DOMAIN, SERVICE_TURN_ON, async_handle_scene_service,
        schema=SCENE_SERVICE_SCHEMA)

    return True


class Scene(Entity):
    """A scene is a group of entities and the states we want them to be."""

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def state(self):
        """Return the state of the scene."""
        return STATE

    def activate(self):
        """Activate scene. Try to get entities into requested state."""
        raise NotImplementedError()

    def async_activate(self):
        """Activate scene. Try to get entities into requested state.

        This method must be run in the event loop and returns a coroutine.
        """
        return self.hass.loop.run_in_executor(None, self.activate)

"""
Event parser and human readable log generator.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/logbook/
"""
import asyncio
import logging
from datetime import timedelta
from itertools import groupby

import voluptuous as vol

from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
from homeassistant.components import recorder, sun
from homeassistant.components.frontend import register_built_in_panel
from homeassistant.components.http import HomeAssistantView
from homeassistant.const import (EVENT_HOMEASSISTANT_START,
                                 EVENT_HOMEASSISTANT_STOP, EVENT_STATE_CHANGED,
                                 STATE_NOT_HOME, STATE_OFF, STATE_ON,
                                 ATTR_HIDDEN, HTTP_BAD_REQUEST)
from homeassistant.core import State, split_entity_id, DOMAIN as HA_DOMAIN
from homeassistant.util.async import run_callback_threadsafe

DOMAIN = "logbook"
DEPENDENCIES = ['recorder', 'frontend']

_LOGGER = logging.getLogger(__name__)

CONF_EXCLUDE = 'exclude'
CONF_INCLUDE = 'include'
CONF_ENTITIES = 'entities'
CONF_DOMAINS = 'domains'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        CONF_EXCLUDE: vol.Schema({
            vol.Optional(CONF_ENTITIES, default=[]): cv.entity_ids,
            vol.Optional(CONF_DOMAINS, default=[]): vol.All(cv.ensure_list,
                                                            [cv.string])
        }),
        CONF_INCLUDE: vol.Schema({
            vol.Optional(CONF_ENTITIES, default=[]): cv.entity_ids,
            vol.Optional(CONF_DOMAINS, default=[]): vol.All(cv.ensure_list,
                                                            [cv.string])
        })
    }),
}, extra=vol.ALLOW_EXTRA)

EVENT_LOGBOOK_ENTRY = 'logbook_entry'

GROUP_BY_MINUTES = 15

ATTR_NAME = 'name'
ATTR_MESSAGE = 'message'
ATTR_DOMAIN = 'domain'
ATTR_ENTITY_ID = 'entity_id'

LOG_MESSAGE_SCHEMA = vol.Schema({
    vol.Required(ATTR_NAME): cv.string,
    vol.Required(ATTR_MESSAGE): cv.template,
    vol.Optional(ATTR_DOMAIN): cv.slug,
    vol.Optional(ATTR_ENTITY_ID): cv.entity_id,
})


def log_entry(hass, name, message, domain=None, entity_id=None):
    """Add an entry to the logbook."""
    run_callback_threadsafe(
        hass.loop, async_log_entry, hass, name, message, domain, entity_id
        ).result()


def async_log_entry(hass, name, message, domain=None, entity_id=None):
    """Add an entry to the logbook."""
    data = {
        ATTR_NAME: name,
        ATTR_MESSAGE: message
    }

    if domain is not None:
        data[ATTR_DOMAIN] = domain
    if entity_id is not None:
        data[ATTR_ENTITY_ID] = entity_id
    hass.bus.async_fire(EVENT_LOGBOOK_ENTRY, data)


def setup(hass, config):
    """Listen for download events to download files."""
    @callback
    def log_message(service):
        """Handle sending notification message service calls."""
        message = service.data[ATTR_MESSAGE]
        name = service.data[ATTR_NAME]
        domain = service.data.get(ATTR_DOMAIN)
        entity_id = service.data.get(ATTR_ENTITY_ID)

        message.hass = hass
        message = message.async_render()
        async_log_entry(hass, name, message, domain, entity_id)

    hass.http.register_view(LogbookView(config))

    register_built_in_panel(hass, 'logbook', 'Logbook',
                            'mdi:format-list-bulleted-type')

    hass.services.register(DOMAIN, 'log', log_message,
                           schema=LOG_MESSAGE_SCHEMA)
    return True


class LogbookView(HomeAssistantView):
    """Handle logbook view requests."""

    url = '/api/logbook'
    name = 'api:logbook'
    extra_urls = ['/api/logbook/{datetime}']

    def __init__(self, config):
        """Initilalize the logbook view."""
        self.config = config

    @asyncio.coroutine
    def get(self, request, datetime=None):
        """Retrieve logbook entries."""
        if datetime:
            datetime = dt_util.parse_datetime(datetime)

            if datetime is None:
                return self.json_message('Invalid datetime', HTTP_BAD_REQUEST)
        else:
            datetime = dt_util.start_of_local_day()

        start_day = dt_util.as_utc(datetime)
        end_day = start_day + timedelta(days=1)

        def get_results():
            """Query DB for results."""
            events = recorder.get_model('Events')
            query = recorder.query('Events').order_by(
                events.time_fired).filter(
                    (events.time_fired > start_day) &
                    (events.time_fired < end_day))
            events = recorder.execute(query)
            return _exclude_events(events, self.config)

        events = yield from request.app['hass'].loop.run_in_executor(
            None, get_results)

        return self.json(humanify(events))


class Entry(object):
    """A human readable version of the log."""

    def __init__(self, when=None, name=None, message=None, domain=None,
                 entity_id=None):
        """Initialize the entry."""
        self.when = when
        self.name = name
        self.message = message
        self.domain = domain
        self.entity_id = entity_id

    def as_dict(self):
        """Convert entry to a dict to be used within JSON."""
        return {
            'when': self.when,
            'name': self.name,
            'message': self.message,
            'domain': self.domain,
            'entity_id': self.entity_id,
        }


def humanify(events):
    """Generator that converts a list of events into Entry objects.

    Will try to group events if possible:
     - if 2+ sensor updates in GROUP_BY_MINUTES, show last
     - if home assistant stop and start happen in same minute call it restarted
    """
    # Group events in batches of GROUP_BY_MINUTES
    for _, g_events in groupby(
            events,
            lambda event: event.time_fired.minute // GROUP_BY_MINUTES):

        events_batch = list(g_events)

        # Keep track of last sensor states
        last_sensor_event = {}

        # Group HA start/stop events
        # Maps minute of event to 1: stop, 2: stop + start
        start_stop_events = {}

        # Process events
        for event in events_batch:
            if event.event_type == EVENT_STATE_CHANGED:
                entity_id = event.data.get('entity_id')

                if entity_id is None:
                    continue

                if entity_id.startswith('sensor.'):
                    last_sensor_event[entity_id] = event

            elif event.event_type == EVENT_HOMEASSISTANT_STOP:
                if event.time_fired.minute in start_stop_events:
                    continue

                start_stop_events[event.time_fired.minute] = 1

            elif event.event_type == EVENT_HOMEASSISTANT_START:
                if event.time_fired.minute not in start_stop_events:
                    continue

                start_stop_events[event.time_fired.minute] = 2

        # Yield entries
        for event in events_batch:
            if event.event_type == EVENT_STATE_CHANGED:

                to_state = State.from_dict(event.data.get('new_state'))

                # If last_changed != last_updated only attributes have changed
                # we do not report on that yet. Also filter auto groups.
                if not to_state or \
                   to_state.last_changed != to_state.last_updated or \
                   to_state.domain == 'group' and \
                   to_state.attributes.get('auto', False):
                    continue

                domain = to_state.domain

                # Skip all but the last sensor state
                if domain == 'sensor' and \
                   event != last_sensor_event[to_state.entity_id]:
                    continue

                # Don't show continuous sensor value changes in the logbook
                if domain == 'sensor' and \
                   to_state.attributes.get('unit_of_measurement'):
                    continue

                yield Entry(
                    event.time_fired,
                    name=to_state.name,
                    message=_entry_message_from_state(domain, to_state),
                    domain=domain,
                    entity_id=to_state.entity_id)

            elif event.event_type == EVENT_HOMEASSISTANT_START:
                if start_stop_events.get(event.time_fired.minute) == 2:
                    continue

                yield Entry(
                    event.time_fired, "Home Assistant", "started",
                    domain=HA_DOMAIN)

            elif event.event_type == EVENT_HOMEASSISTANT_STOP:
                if start_stop_events.get(event.time_fired.minute) == 2:
                    action = "restarted"
                else:
                    action = "stopped"

                yield Entry(
                    event.time_fired, "Home Assistant", action,
                    domain=HA_DOMAIN)

            elif event.event_type == EVENT_LOGBOOK_ENTRY:
                domain = event.data.get(ATTR_DOMAIN)
                entity_id = event.data.get(ATTR_ENTITY_ID)
                if domain is None and entity_id is not None:
                    try:
                        domain = split_entity_id(str(entity_id))[0]
                    except IndexError:
                        pass

                yield Entry(
                    event.time_fired, event.data.get(ATTR_NAME),
                    event.data.get(ATTR_MESSAGE), domain,
                    entity_id)


def _exclude_events(events, config):
    """Get lists of excluded entities and platforms."""
    excluded_entities = []
    excluded_domains = []
    included_entities = []
    included_domains = []
    exclude = config[DOMAIN].get(CONF_EXCLUDE)
    if exclude:
        excluded_entities = exclude[CONF_ENTITIES]
        excluded_domains = exclude[CONF_DOMAINS]
    include = config[DOMAIN].get(CONF_INCLUDE)
    if include:
        included_entities = include[CONF_ENTITIES]
        included_domains = include[CONF_DOMAINS]

    filtered_events = []
    for event in events:
        domain, entity_id = None, None

        if event.event_type == EVENT_STATE_CHANGED:
            to_state = State.from_dict(event.data.get('new_state'))
            # Do not report on new entities
            if not to_state:
                continue

            # exclude entities which are customized hidden
            hidden = to_state.attributes.get(ATTR_HIDDEN, False)
            if hidden:
                continue

            domain = to_state.domain
            entity_id = to_state.entity_id

        elif event.event_type == EVENT_LOGBOOK_ENTRY:
            domain = event.data.get(ATTR_DOMAIN)
            entity_id = event.data.get(ATTR_ENTITY_ID)

        if domain or entity_id:
            # filter if only excluded is configured for this domain
            if excluded_domains and domain in excluded_domains and \
                    not included_domains:
                if (included_entities and entity_id not in included_entities) \
                        or not included_entities:
                    continue
            # filter if only included is configured for this domain
            elif not excluded_domains and included_domains and \
                    domain not in included_domains:
                if (included_entities and entity_id not in included_entities) \
                        or not included_entities:
                    continue
            # filter if included and excluded is configured for this domain
            elif excluded_domains and included_domains and \
                    (domain not in included_domains or
                     domain in excluded_domains):
                if (included_entities and entity_id not in included_entities) \
                        or not included_entities or domain in excluded_domains:
                    continue
            # filter if only included is configured for this entity
            elif not excluded_domains and not included_domains and \
                    included_entities and entity_id not in included_entities:
                continue
            # check if logbook entry is excluded for this entity
            if entity_id in excluded_entities:
                continue
        filtered_events.append(event)
    return filtered_events


# pylint: disable=too-many-return-statements
def _entry_message_from_state(domain, state):
    """Convert a state to a message for the logbook."""
    # We pass domain in so we don't have to split entity_id again
    if domain == 'device_tracker':
        if state.state == STATE_NOT_HOME:
            return 'is away'
        else:
            return 'is at {}'.format(state.state)

    elif domain == 'sun':
        if state.state == sun.STATE_ABOVE_HORIZON:
            return 'has risen'
        else:
            return 'has set'

    elif state.state == STATE_ON:
        # Future: combine groups and its entity entries ?
        return "turned on"

    elif state.state == STATE_OFF:
        return "turned off"

    return "changed to {}".format(state.state)

"""
Core components of Home Assistant.

Home Assistant is a Home Automation framework for observing the state
of entities and react to changes.
"""
# pylint: disable=unused-import, too-many-lines
import asyncio
from concurrent.futures import ThreadPoolExecutor
import enum
import logging
import os
import re
import signal
import sys
import threading

from types import MappingProxyType
from typing import Optional, Any, Callable, List  # NOQA

import voluptuous as vol
from voluptuous.humanize import humanize_error

from homeassistant.const import (
    ATTR_DOMAIN, ATTR_FRIENDLY_NAME, ATTR_NOW, ATTR_SERVICE,
    ATTR_SERVICE_CALL_ID, ATTR_SERVICE_DATA, EVENT_CALL_SERVICE,
    EVENT_HOMEASSISTANT_START, EVENT_HOMEASSISTANT_STOP,
    EVENT_SERVICE_EXECUTED, EVENT_SERVICE_REGISTERED, EVENT_STATE_CHANGED,
    EVENT_TIME_CHANGED, MATCH_ALL, RESTART_EXIT_CODE,
    SERVICE_HOMEASSISTANT_RESTART, SERVICE_HOMEASSISTANT_STOP, __version__)
from homeassistant.exceptions import (
    HomeAssistantError, InvalidEntityFormatError, ShuttingDown)
from homeassistant.util.async import (
    run_coroutine_threadsafe, run_callback_threadsafe)
import homeassistant.util as util
import homeassistant.util.dt as dt_util
import homeassistant.util.location as location
from homeassistant.util.unit_system import UnitSystem, METRIC_SYSTEM  # NOQA

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

DOMAIN = "homeassistant"

# How often time_changed event should fire
TIMER_INTERVAL = 1  # seconds

# How long we wait for the result of a service call
SERVICE_CALL_LIMIT = 10  # seconds

# Pattern for validating entity IDs (format: <domain>.<entity>)
ENTITY_ID_PATTERN = re.compile(r"^(\w+)\.(\w+)$")

# Size of a executor pool
EXECUTOR_POOL_SIZE = 10

# AsyncHandler for logging
DATA_ASYNCHANDLER = 'log_asynchandler'

_LOGGER = logging.getLogger(__name__)


def split_entity_id(entity_id: str) -> List[str]:
    """Split a state entity_id into domain, object_id."""
    return entity_id.split(".", 1)


def valid_entity_id(entity_id: str) -> bool:
    """Test if an entity ID is a valid format."""
    return ENTITY_ID_PATTERN.match(entity_id) is not None


def callback(func: Callable[..., None]) -> Callable[..., None]:
    """Annotation to mark method as safe to call from within the event loop."""
    # pylint: disable=protected-access
    func._hass_callback = True
    return func


def is_callback(func: Callable[..., Any]) -> bool:
    """Check if function is safe to be called in the event loop."""
    return '_hass_callback' in func.__dict__


class CoreState(enum.Enum):
    """Represent the current state of Home Assistant."""

    not_running = "NOT_RUNNING"
    starting = "STARTING"
    running = "RUNNING"
    stopping = "STOPPING"

    def __str__(self) -> str:
        """Return the event."""
        return self.value


class HomeAssistant(object):
    """Root object of the Home Assistant home automation."""

    def __init__(self, loop=None):
        """Initialize new Home Assistant object."""
        if sys.platform == "win32":
            self.loop = loop or asyncio.ProactorEventLoop()
        else:
            self.loop = loop or asyncio.get_event_loop()

        self.executor = ThreadPoolExecutor(max_workers=EXECUTOR_POOL_SIZE)
        self.loop.set_default_executor(self.executor)
        self.loop.set_exception_handler(self._async_exception_handler)
        self._pending_tasks = []
        self.bus = EventBus(self)
        self.services = ServiceRegistry(self)
        self.states = StateMachine(self.bus, self.loop)
        self.config = Config()  # type: Config
        # This is a dictionary that any component can store any data on.
        self.data = {}
        self.state = CoreState.not_running
        self.exit_code = None

    @property
    def is_running(self) -> bool:
        """Return if Home Assistant is running."""
        return self.state in (CoreState.starting, CoreState.running)

    def start(self) -> None:
        """Start home assistant."""
        # Register the async start
        self.loop.create_task(self.async_start())

        # Run forever and catch keyboard interrupt
        try:
            # Block until stopped
            _LOGGER.info("Starting Home Assistant core loop")
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.loop.call_soon(self._async_stop_handler)
            self.loop.run_forever()
        finally:
            self.loop.close()

    @asyncio.coroutine
    def async_start(self):
        """Finalize startup from inside the event loop.

        This method is a coroutine.
        """
        _LOGGER.info("Starting Home Assistant")

        self.state = CoreState.starting

        # Register the restart/stop event
        self.services.async_register(
            DOMAIN, SERVICE_HOMEASSISTANT_STOP, self._async_stop_handler)
        self.services.async_register(
            DOMAIN, SERVICE_HOMEASSISTANT_RESTART, self._async_restart_handler)

        # Setup signal handling
        if sys.platform != 'win32':
            try:
                self.loop.add_signal_handler(
                    signal.SIGTERM, self._async_stop_handler)
            except ValueError:
                _LOGGER.warning('Could not bind to SIGTERM.')

            try:
                self.loop.add_signal_handler(
                    signal.SIGHUP, self._async_restart_handler)
            except ValueError:
                _LOGGER.warning('Could not bind to SIGHUP.')

        # pylint: disable=protected-access
        self.loop._thread_ident = threading.get_ident()
        _async_create_timer(self)
        self.bus.async_fire(EVENT_HOMEASSISTANT_START)
        self.state = CoreState.running

    def add_job(self, target: Callable[..., None], *args: Any) -> None:
        """Add job to the executor pool.

        target: target to call.
        args: parameters for method to call.
        """
        if target is None:
            raise ValueError("Don't call add_job with None.")
        self.loop.call_soon_threadsafe(self.async_add_job, target, *args)

    @callback
    def _async_add_job(self, target: Callable[..., None], *args: Any) -> None:
        """Add a job from within the eventloop.

        This method must be run in the event loop.

        target: target to call.
        args: parameters for method to call.
        """
        if asyncio.iscoroutine(target):
            self.loop.create_task(target)
        elif is_callback(target):
            self.loop.call_soon(target, *args)
        elif asyncio.iscoroutinefunction(target):
            self.loop.create_task(target(*args))
        else:
            self.loop.run_in_executor(None, target, *args)

    async_add_job = _async_add_job

    @callback
    def _async_add_job_tracking(self, target: Callable[..., None],
                                *args: Any) -> None:
        """Add a job from within the eventloop.

        This method must be run in the event loop.

        target: target to call.
        args: parameters for method to call.
        """
        task = None

        if asyncio.iscoroutine(target):
            task = self.loop.create_task(target)
        elif is_callback(target):
            self.loop.call_soon(target, *args)
        elif asyncio.iscoroutinefunction(target):
            task = self.loop.create_task(target(*args))
        else:
            task = self.loop.run_in_executor(None, target, *args)

        # if a task is sheduled
        if task is not None:
            self._pending_tasks.append(task)

    @callback
    def async_track_tasks(self):
        """Track tasks so you can wait for all tasks to be done."""
        self.async_add_job = self._async_add_job_tracking

    @asyncio.coroutine
    def async_stop_track_tasks(self):
        """Track tasks so you can wait for all tasks to be done."""
        yield from self.async_block_till_done()
        self.async_add_job = self._async_add_job

    @callback
    def async_run_job(self, target: Callable[..., None], *args: Any) -> None:
        """Run a job from within the event loop.

        This method must be run in the event loop.

        target: target to call.
        args: parameters for method to call.
        """
        if is_callback(target):
            target(*args)
        else:
            self.async_add_job(target, *args)

    def block_till_done(self) -> None:
        """Block till all pending work is done."""
        run_coroutine_threadsafe(
            self.async_block_till_done(), loop=self.loop).result()

    @asyncio.coroutine
    def async_block_till_done(self):
        """Block till all pending work is done."""
        # To flush out any call_soon_threadsafe
        yield from asyncio.sleep(0, loop=self.loop)

        while self._pending_tasks:
            pending = [task for task in self._pending_tasks
                       if not task.done()]
            self._pending_tasks.clear()
            if len(pending) > 0:
                yield from asyncio.wait(pending, loop=self.loop)
            else:
                yield from asyncio.sleep(0, loop=self.loop)

    def stop(self) -> None:
        """Stop Home Assistant and shuts down all threads."""
        run_coroutine_threadsafe(self.async_stop(), self.loop)

    @asyncio.coroutine
    def async_stop(self) -> None:
        """Stop Home Assistant and shuts down all threads.

        This method is a coroutine.
        """
        import homeassistant.helpers.aiohttp_client as aiohttp_client

        self.state = CoreState.stopping
        self.async_track_tasks()
        self.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
        yield from self.async_block_till_done()
        self.executor.shutdown()
        self.state = CoreState.not_running

        # cleanup connector pool from aiohttp
        yield from aiohttp_client.async_cleanup_websession(self)

        # cleanup async layer from python logging
        if self.data.get(DATA_ASYNCHANDLER):
            handler = self.data.pop(DATA_ASYNCHANDLER)
            logging.getLogger('').removeHandler(handler)
            yield from handler.async_close(blocking=True)

        self.loop.stop()

    # pylint: disable=no-self-use
    @callback
    def _async_exception_handler(self, loop, context):
        """Handle all exception inside the core loop."""
        kwargs = {}
        exception = context.get('exception')
        if exception:
            # Do not report on shutting down exceptions.
            if isinstance(exception, ShuttingDown):
                return

            kwargs['exc_info'] = (type(exception), exception,
                                  exception.__traceback__)

        _LOGGER.error('Error doing job: %s', context['message'],
                      **kwargs)

    @callback
    def _async_stop_handler(self, *args):
        """Stop Home Assistant."""
        self.exit_code = 0
        self.loop.create_task(self.async_stop())

    @callback
    def _async_restart_handler(self, *args):
        """Restart Home Assistant."""
        self.exit_code = RESTART_EXIT_CODE
        self.loop.create_task(self.async_stop())


class EventOrigin(enum.Enum):
    """Represent the origin of an event."""

    local = "LOCAL"
    remote = "REMOTE"

    def __str__(self):
        """Return the event."""
        return self.value


class Event(object):
    """Represents an event within the Bus."""

    __slots__ = ['event_type', 'data', 'origin', 'time_fired']

    def __init__(self, event_type, data=None, origin=EventOrigin.local,
                 time_fired=None):
        """Initialize a new event."""
        self.event_type = event_type
        self.data = data or {}
        self.origin = origin
        self.time_fired = time_fired or dt_util.utcnow()

    def as_dict(self):
        """Create a dict representation of this Event.

        Async friendly.
        """
        return {
            'event_type': self.event_type,
            'data': dict(self.data),
            'origin': str(self.origin),
            'time_fired': self.time_fired,
        }

    def __repr__(self):
        """Return the representation."""
        # pylint: disable=maybe-no-member
        if self.data:
            return "<Event {}[{}]: {}>".format(
                self.event_type, str(self.origin)[0],
                util.repr_helper(self.data))
        else:
            return "<Event {}[{}]>".format(self.event_type,
                                           str(self.origin)[0])

    def __eq__(self, other):
        """Return the comparison."""
        return (self.__class__ == other.__class__ and
                self.event_type == other.event_type and
                self.data == other.data and
                self.origin == other.origin and
                self.time_fired == other.time_fired)


class EventBus(object):
    """Allows firing of and listening for events."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize a new event bus."""
        self._listeners = {}
        self._hass = hass

    @callback
    def async_listeners(self):
        """Dict with events and the number of listeners.

        This method must be run in the event loop.
        """
        return {key: len(self._listeners[key])
                for key in self._listeners}

    @property
    def listeners(self):
        """Dict with events and the number of listeners."""
        return run_callback_threadsafe(
            self._hass.loop, self.async_listeners
        ).result()

    def fire(self, event_type: str, event_data=None, origin=EventOrigin.local):
        """Fire an event."""
        self._hass.loop.call_soon_threadsafe(self.async_fire, event_type,
                                             event_data, origin)

    @callback
    def async_fire(self, event_type: str, event_data=None,
                   origin=EventOrigin.local, wait=False):
        """Fire an event.

        This method must be run in the event loop.
        """
        if event_type != EVENT_HOMEASSISTANT_STOP and \
                self._hass.state == CoreState.stopping:
            raise ShuttingDown('Home Assistant is shutting down.')

        # Copy the list of the current listeners because some listeners
        # remove themselves as a listener while being executed which
        # causes the iterator to be confused.
        get = self._listeners.get
        listeners = get(MATCH_ALL, []) + get(event_type, [])

        event = Event(event_type, event_data, origin)

        if event_type != EVENT_TIME_CHANGED:
            _LOGGER.info("Bus:Handling %s", event)

        if not listeners:
            return

        for func in listeners:
            self._hass.async_add_job(func, event)

    def listen(self, event_type, listener):
        """Listen for all events or events of a specific type.

        To listen to all events specify the constant ``MATCH_ALL``
        as event_type.
        """
        async_remove_listener = run_callback_threadsafe(
            self._hass.loop, self.async_listen, event_type, listener).result()

        def remove_listener():
            """Remove the listener."""
            run_callback_threadsafe(
                self._hass.loop, async_remove_listener).result()

        return remove_listener

    @callback
    def async_listen(self, event_type, listener):
        """Listen for all events or events of a specific type.

        To listen to all events specify the constant ``MATCH_ALL``
        as event_type.

        This method must be run in the event loop.
        """
        if event_type in self._listeners:
            self._listeners[event_type].append(listener)
        else:
            self._listeners[event_type] = [listener]

        def remove_listener():
            """Remove the listener."""
            self._async_remove_listener(event_type, listener)

        return remove_listener

    def listen_once(self, event_type, listener):
        """Listen once for event of a specific type.

        To listen to all events specify the constant ``MATCH_ALL``
        as event_type.

        Returns function to unsubscribe the listener.
        """
        async_remove_listener = run_callback_threadsafe(
            self._hass.loop, self.async_listen_once, event_type, listener,
        ).result()

        def remove_listener():
            """Remove the listener."""
            run_callback_threadsafe(
                self._hass.loop, async_remove_listener).result()

        return remove_listener

    @callback
    def async_listen_once(self, event_type, listener):
        """Listen once for event of a specific type.

        To listen to all events specify the constant ``MATCH_ALL``
        as event_type.

        Returns registered listener that can be used with remove_listener.

        This method must be run in the event loop.
        """
        @callback
        def onetime_listener(event):
            """Remove listener from eventbus and then fire listener."""
            if hasattr(onetime_listener, 'run'):
                return
            # Set variable so that we will never run twice.
            # Because the event bus loop might have async_fire queued multiple
            # times, its possible this listener may already be lined up
            # multiple times as well.
            # This will make sure the second time it does nothing.
            setattr(onetime_listener, 'run', True)
            self._async_remove_listener(event_type, onetime_listener)

            self._hass.async_run_job(listener, event)

        return self.async_listen(event_type, onetime_listener)

    @callback
    def _async_remove_listener(self, event_type, listener):
        """Remove a listener of a specific event_type.

        This method must be run in the event loop.
        """
        try:
            self._listeners[event_type].remove(listener)

            # delete event_type list if empty
            if not self._listeners[event_type]:
                self._listeners.pop(event_type)
        except (KeyError, ValueError):
            # KeyError is key event_type listener did not exist
            # ValueError if listener did not exist within event_type
            _LOGGER.warning('Unable to remove unknown listener %s',
                            listener)


class State(object):
    """Object to represent a state within the state machine.

    entity_id: the entity that is represented.
    state: the state of the entity
    attributes: extra information on entity and state
    last_changed: last time the state was changed, not the attributes.
    last_updated: last time this object was updated.
    """

    __slots__ = ['entity_id', 'state', 'attributes',
                 'last_changed', 'last_updated']

    def __init__(self, entity_id, state, attributes=None, last_changed=None,
                 last_updated=None):
        """Initialize a new state."""
        if not valid_entity_id(entity_id):
            raise InvalidEntityFormatError((
                "Invalid entity id encountered: {}. "
                "Format should be <domain>.<object_id>").format(entity_id))

        self.entity_id = entity_id.lower()
        self.state = str(state)
        self.attributes = MappingProxyType(attributes or {})
        self.last_updated = last_updated or dt_util.utcnow()

        self.last_changed = last_changed or self.last_updated

    @property
    def domain(self):
        """Domain of this state."""
        return split_entity_id(self.entity_id)[0]

    @property
    def object_id(self):
        """Object id of this state."""
        return split_entity_id(self.entity_id)[1]

    @property
    def name(self):
        """Name of this state."""
        return (
            self.attributes.get(ATTR_FRIENDLY_NAME) or
            self.object_id.replace('_', ' '))

    def as_dict(self):
        """Return a dict representation of the State.

        Async friendly.

        To be used for JSON serialization.
        Ensures: state == State.from_dict(state.as_dict())
        """
        return {'entity_id': self.entity_id,
                'state': self.state,
                'attributes': dict(self.attributes),
                'last_changed': self.last_changed,
                'last_updated': self.last_updated}

    @classmethod
    def from_dict(cls, json_dict):
        """Initialize a state from a dict.

        Async friendly.

        Ensures: state == State.from_json_dict(state.to_json_dict())
        """
        if not (json_dict and 'entity_id' in json_dict and
                'state' in json_dict):
            return None

        last_changed = json_dict.get('last_changed')

        if isinstance(last_changed, str):
            last_changed = dt_util.parse_datetime(last_changed)

        last_updated = json_dict.get('last_updated')

        if isinstance(last_updated, str):
            last_updated = dt_util.parse_datetime(last_updated)

        return cls(json_dict['entity_id'], json_dict['state'],
                   json_dict.get('attributes'), last_changed, last_updated)

    def __eq__(self, other):
        """Return the comparison of the state."""
        return (self.__class__ == other.__class__ and
                self.entity_id == other.entity_id and
                self.state == other.state and
                self.attributes == other.attributes)

    def __repr__(self):
        """Return the representation of the states."""
        attr = "; {}".format(util.repr_helper(self.attributes)) \
               if self.attributes else ""

        return "<state {}={}{} @ {}>".format(
            self.entity_id, self.state, attr,
            dt_util.as_local(self.last_changed).isoformat())


class StateMachine(object):
    """Helper class that tracks the state of different entities."""

    def __init__(self, bus, loop):
        """Initialize state machine."""
        self._states = {}
        self._bus = bus
        self._loop = loop

    def entity_ids(self, domain_filter=None):
        """List of entity ids that are being tracked."""
        future = run_callback_threadsafe(
            self._loop, self.async_entity_ids, domain_filter
        )
        return future.result()

    @callback
    def async_entity_ids(self, domain_filter=None):
        """List of entity ids that are being tracked.

        This method must be run in the event loop.
        """
        if domain_filter is None:
            return list(self._states.keys())

        domain_filter = domain_filter.lower()

        return [state.entity_id for state in list(self._states.values())
                if state.domain == domain_filter]

    def all(self):
        """Create a list of all states."""
        return run_callback_threadsafe(self._loop, self.async_all).result()

    @callback
    def async_all(self):
        """Create a list of all states.

        This method must be run in the event loop.
        """
        return list(self._states.values())

    def get(self, entity_id):
        """Retrieve state of entity_id or None if not found.

        Async friendly.
        """
        return self._states.get(entity_id.lower())

    def is_state(self, entity_id, state):
        """Test if entity exists and is specified state.

        Async friendly.
        """
        state_obj = self.get(entity_id)

        return state_obj and state_obj.state == state

    def is_state_attr(self, entity_id, name, value):
        """Test if entity exists and has a state attribute set to value.

        Async friendly.
        """
        state_obj = self.get(entity_id)

        return state_obj and state_obj.attributes.get(name, None) == value

    def remove(self, entity_id):
        """Remove the state of an entity.

        Returns boolean to indicate if an entity was removed.
        """
        return run_callback_threadsafe(
            self._loop, self.async_remove, entity_id).result()

    @callback
    def async_remove(self, entity_id):
        """Remove the state of an entity.

        Returns boolean to indicate if an entity was removed.

        This method must be run in the event loop.
        """
        entity_id = entity_id.lower()

        old_state = self._states.pop(entity_id, None)

        if old_state is None:
            return False

        event_data = {
            'entity_id': entity_id,
            'old_state': old_state,
            'new_state': None,
        }

        self._bus.async_fire(EVENT_STATE_CHANGED, event_data)

        return True

    def set(self, entity_id, new_state, attributes=None, force_update=False):
        """Set the state of an entity, add entity if it does not exist.

        Attributes is an optional dict to specify attributes of this state.

        If you just update the attributes and not the state, last changed will
        not be affected.
        """
        run_callback_threadsafe(
            self._loop,
            self.async_set, entity_id, new_state, attributes, force_update,
        ).result()

    @callback
    def async_set(self, entity_id, new_state, attributes=None,
                  force_update=False):
        """Set the state of an entity, add entity if it does not exist.

        Attributes is an optional dict to specify attributes of this state.

        If you just update the attributes and not the state, last changed will
        not be affected.

        This method must be run in the event loop.
        """
        entity_id = entity_id.lower()
        new_state = str(new_state)
        attributes = attributes or {}

        old_state = self._states.get(entity_id)

        is_existing = old_state is not None
        same_state = (is_existing and old_state.state == new_state and
                      not force_update)
        same_attr = is_existing and old_state.attributes == attributes

        if same_state and same_attr:
            return

        # If state did not exist or is different, set it
        last_changed = old_state.last_changed if same_state else None

        state = State(entity_id, new_state, attributes, last_changed)
        self._states[entity_id] = state

        event_data = {
            'entity_id': entity_id,
            'old_state': old_state,
            'new_state': state,
        }

        self._bus.async_fire(EVENT_STATE_CHANGED, event_data)


class Service(object):
    """Represents a callable service."""

    __slots__ = ['func', 'description', 'fields', 'schema',
                 'is_callback', 'is_coroutinefunction']

    def __init__(self, func, description, fields, schema):
        """Initialize a service."""
        self.func = func
        self.description = description or ''
        self.fields = fields or {}
        self.schema = schema
        self.is_callback = is_callback(func)
        self.is_coroutinefunction = asyncio.iscoroutinefunction(func)

    def as_dict(self):
        """Return dictionary representation of this service."""
        return {
            'description': self.description,
            'fields': self.fields,
        }


class ServiceCall(object):
    """Represents a call to a service."""

    __slots__ = ['domain', 'service', 'data', 'call_id']

    def __init__(self, domain, service, data=None, call_id=None):
        """Initialize a service call."""
        self.domain = domain.lower()
        self.service = service.lower()
        self.data = MappingProxyType(data or {})
        self.call_id = call_id

    def __repr__(self):
        """Return the represenation of the service."""
        if self.data:
            return "<ServiceCall {}.{}: {}>".format(
                self.domain, self.service, util.repr_helper(self.data))
        else:
            return "<ServiceCall {}.{}>".format(self.domain, self.service)


class ServiceRegistry(object):
    """Offers services over the eventbus."""

    def __init__(self, hass):
        """Initialize a service registry."""
        self._services = {}
        self._hass = hass
        self._cur_id = 0
        self._async_unsub_call_event = None

    @property
    def services(self):
        """Dict with per domain a list of available services."""
        return run_callback_threadsafe(
            self._hass.loop, self.async_services,
        ).result()

    @callback
    def async_services(self):
        """Dict with per domain a list of available services.

        This method must be run in the event loop.
        """
        return {domain: {key: value.as_dict() for key, value
                         in list(self._services[domain].items())}
                for domain in self._services}

    def has_service(self, domain, service):
        """Test if specified service exists.

        Async friendly.
        """
        return service.lower() in self._services.get(domain.lower(), [])

    def register(self, domain, service, service_func, description=None,
                 schema=None):
        """
        Register a service.

        Description is a dict containing key 'description' to describe
        the service and a key 'fields' to describe the fields.

        Schema is called to coerce and validate the service data.
        """
        run_callback_threadsafe(
            self._hass.loop,
            self.async_register, domain, service, service_func, description,
            schema
        ).result()

    @callback
    def async_register(self, domain, service, service_func, description=None,
                       schema=None):
        """
        Register a service.

        Description is a dict containing key 'description' to describe
        the service and a key 'fields' to describe the fields.

        Schema is called to coerce and validate the service data.

        This method must be run in the event loop.
        """
        domain = domain.lower()
        service = service.lower()
        description = description or {}
        service_obj = Service(service_func, description.get('description'),
                              description.get('fields', {}), schema)

        if domain in self._services:
            self._services[domain][service] = service_obj
        else:
            self._services[domain] = {service: service_obj}

        if self._async_unsub_call_event is None:
            self._async_unsub_call_event = self._hass.bus.async_listen(
                EVENT_CALL_SERVICE, self._event_to_service_call)

        self._hass.bus.async_fire(
            EVENT_SERVICE_REGISTERED,
            {ATTR_DOMAIN: domain, ATTR_SERVICE: service}
        )

    def call(self, domain, service, service_data=None, blocking=False):
        """
        Call a service.

        Specify blocking=True to wait till service is executed.
        Waits a maximum of SERVICE_CALL_LIMIT.

        If blocking = True, will return boolean if service executed
        succesfully within SERVICE_CALL_LIMIT.

        This method will fire an event to call the service.
        This event will be picked up by this ServiceRegistry and any
        other ServiceRegistry that is listening on the EventBus.

        Because the service is sent as an event you are not allowed to use
        the keys ATTR_DOMAIN and ATTR_SERVICE in your service_data.
        """
        return run_coroutine_threadsafe(
            self.async_call(domain, service, service_data, blocking),
            self._hass.loop
        ).result()

    @asyncio.coroutine
    def async_call(self, domain, service, service_data=None, blocking=False):
        """
        Call a service.

        Specify blocking=True to wait till service is executed.
        Waits a maximum of SERVICE_CALL_LIMIT.

        If blocking = True, will return boolean if service executed
        succesfully within SERVICE_CALL_LIMIT.

        This method will fire an event to call the service.
        This event will be picked up by this ServiceRegistry and any
        other ServiceRegistry that is listening on the EventBus.

        Because the service is sent as an event you are not allowed to use
        the keys ATTR_DOMAIN and ATTR_SERVICE in your service_data.

        This method is a coroutine.
        """
        call_id = self._generate_unique_id()

        event_data = {
            ATTR_DOMAIN: domain.lower(),
            ATTR_SERVICE: service.lower(),
            ATTR_SERVICE_DATA: service_data,
            ATTR_SERVICE_CALL_ID: call_id,
        }

        if blocking:
            fut = asyncio.Future(loop=self._hass.loop)

            @callback
            def service_executed(event):
                """Callback method that is called when service is executed."""
                if event.data[ATTR_SERVICE_CALL_ID] == call_id:
                    fut.set_result(True)

            unsub = self._hass.bus.async_listen(EVENT_SERVICE_EXECUTED,
                                                service_executed)

        self._hass.bus.async_fire(EVENT_CALL_SERVICE, event_data)

        if blocking:
            done, _ = yield from asyncio.wait([fut], loop=self._hass.loop,
                                              timeout=SERVICE_CALL_LIMIT)
            success = bool(done)
            unsub()
            return success

    @asyncio.coroutine
    def _event_to_service_call(self, event):
        """Callback for SERVICE_CALLED events from the event bus."""
        service_data = event.data.get(ATTR_SERVICE_DATA) or {}
        domain = event.data.get(ATTR_DOMAIN).lower()
        service = event.data.get(ATTR_SERVICE).lower()
        call_id = event.data.get(ATTR_SERVICE_CALL_ID)

        if not self.has_service(domain, service):
            if event.origin == EventOrigin.local:
                _LOGGER.warning('Unable to find service %s/%s',
                                domain, service)
            return

        service_handler = self._services[domain][service]

        def fire_service_executed():
            """Fire service executed event."""
            if not call_id:
                return

            data = {ATTR_SERVICE_CALL_ID: call_id}

            if (service_handler.is_coroutinefunction or
                    service_handler.is_callback):
                self._hass.bus.async_fire(EVENT_SERVICE_EXECUTED, data)
            else:
                self._hass.bus.fire(EVENT_SERVICE_EXECUTED, data)

        try:
            if service_handler.schema:
                service_data = service_handler.schema(service_data)
        except vol.Invalid as ex:
            _LOGGER.error('Invalid service data for %s.%s: %s',
                          domain, service, humanize_error(service_data, ex))
            fire_service_executed()
            return

        service_call = ServiceCall(domain, service, service_data, call_id)

        if service_handler.is_callback:
            service_handler.func(service_call)
            fire_service_executed()
        elif service_handler.is_coroutinefunction:
            yield from service_handler.func(service_call)
            fire_service_executed()
        else:
            def execute_service():
                """Execute a service and fires a SERVICE_EXECUTED event."""
                service_handler.func(service_call)
                fire_service_executed()

            self._hass.async_add_job(execute_service)

    def _generate_unique_id(self):
        """Generate a unique service call id."""
        self._cur_id += 1
        return "{}-{}".format(id(self), self._cur_id)


class Config(object):
    """Configuration settings for Home Assistant."""

    def __init__(self):
        """Initialize a new config object."""
        self.latitude = None  # type: Optional[float]
        self.longitude = None  # type: Optional[float]
        self.elevation = None  # type: Optional[int]
        self.location_name = None  # type: Optional[str]
        self.time_zone = None  # type: Optional[str]
        self.units = METRIC_SYSTEM  # type: UnitSystem

        # If True, pip install is skipped for requirements on startup
        self.skip_pip = False  # type: bool

        # List of loaded components
        self.components = []

        # Remote.API object pointing at local API
        self.api = None

        # Directory that holds the configuration
        self.config_dir = None

    def distance(self: object, lat: float, lon: float) -> float:
        """Calculate distance from Home Assistant.

        Async friendly.
        """
        return self.units.length(
            location.distance(self.latitude, self.longitude, lat, lon), 'm')

    def path(self, *path):
        """Generate path to the file within the config dir.

        Async friendly.
        """
        if self.config_dir is None:
            raise HomeAssistantError("config_dir is not set")
        return os.path.join(self.config_dir, *path)

    def as_dict(self):
        """Create a dict representation of this dict.

        Async friendly.
        """
        time_zone = self.time_zone or dt_util.UTC

        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'unit_system': self.units.as_dict(),
            'location_name': self.location_name,
            'time_zone': time_zone.zone,
            'components': self.components,
            'config_dir': self.config_dir,
            'version': __version__
        }


def _async_create_timer(hass, interval=TIMER_INTERVAL):
    """Create a timer that will start on HOMEASSISTANT_START."""
    stop_event = asyncio.Event(loop=hass.loop)

    # Setting the Event inside the loop by marking it as a coroutine
    @callback
    def stop_timer(event):
        """Stop the timer."""
        stop_event.set()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_timer)

    @asyncio.coroutine
    def timer(interval, stop_event):
        """Create an async timer."""
        _LOGGER.info("Timer:starting")

        last_fired_on_second = -1

        calc_now = dt_util.utcnow

        while not stop_event.is_set():
            now = calc_now()

            # First check checks if we are not on a second matching the
            # timer interval. Second check checks if we did not already fire
            # this interval.
            if now.second % interval or \
               now.second == last_fired_on_second:

                # Sleep till it is the next time that we have to fire an event.
                # Aim for halfway through the second that fits TIMER_INTERVAL.
                # If TIMER_INTERVAL is 10 fire at .5, 10.5, 20.5, etc seconds.
                # This will yield the best results because time.sleep() is not
                # 100% accurate because of non-realtime OS's
                slp_seconds = interval - now.second % interval + \
                    .5 - now.microsecond/1000000.0

                yield from asyncio.sleep(slp_seconds, loop=hass.loop)

                now = calc_now()

            last_fired_on_second = now.second

            # Event might have been set while sleeping
            if not stop_event.is_set():
                try:
                    # Schedule the bus event
                    hass.loop.call_soon(
                        hass.bus.async_fire,
                        EVENT_TIME_CHANGED,
                        {ATTR_NOW: now}
                    )
                except ShuttingDown:
                    # HA raises error if firing event after it has shut down
                    break

    @asyncio.coroutine
    def start_timer(event):
        """Start our async timer."""
        hass.loop.create_task(timer(interval, stop_event))

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, start_timer)

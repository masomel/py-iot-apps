"""Entity to track connections to stream API."""
import asyncio
import logging

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity


NAME_WS = 'homeassistant.components.websocket_api'
NAME_STREAM = 'homeassistant.components.api'


class StreamHandler(logging.Handler):
    """Check log messages for stream connect/disconnect."""

    def __init__(self, entity):
        """Initialize handler."""
        super().__init__()
        self.entity = entity
        self.count = 0

    def handle(self, record):
        """Handle a log message."""
        if record.name == NAME_STREAM:
            if not record.msg.startswith('STREAM'):
                return

            if record.msg.endswith('ATTACHED'):
                self.entity.count += 1
            elif record.msg.endswith('RESPONSE CLOSED'):
                self.entity.count -= 1

        else:
            if not record.msg.startswith('WS'):
                return
            elif len(record.args) < 2:
                return
            elif record.args[1] == 'Connected':
                self.entity.count += 1
            elif record.args[1] == 'Closed connection':
                self.entity.count -= 1

        self.entity.schedule_update_ha_state()


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the logger for filters."""
    entity = APICount()
    handler = StreamHandler(entity)

    logging.getLogger(NAME_STREAM).addHandler(handler)
    logging.getLogger(NAME_WS).addHandler(handler)

    @callback
    def remove_logger(event):
        """Remove our handlers."""
        logging.getLogger(NAME_STREAM).removeHandler(handler)
        logging.getLogger(NAME_WS).removeHandler(handler)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, remove_logger)

    yield from async_add_devices([entity])


class APICount(Entity):
    """Entity to represent how many people are connected to stream API."""

    def __init__(self):
        """Initialize the API count."""
        self.count = 0

    @property
    def name(self):
        """Return name of entity."""
        return "Connected clients"

    @property
    def state(self):
        """Return current API count."""
        return self.count

    @property
    def unit_of_measurement(self):
        """Unit of measurement."""
        return "clients"

"""
Support for Google Calendar Search binary sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.google_calendar/
"""
# pylint: disable=import-error
import logging
from datetime import timedelta

from homeassistant.components.calendar import CalendarEventDevice
from homeassistant.components.google import (CONF_CAL_ID, CONF_ENTITIES,
                                             CONF_TRACK, TOKEN_FILE,
                                             GoogleCalendarService)
from homeassistant.util import Throttle, dt

DEFAULT_GOOGLE_SEARCH_PARAMS = {
    'orderBy': 'startTime',
    'maxResults': 1,
    'singleEvents': True,
}

# Return cached results if last scan was less then this time ago
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=15)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, disc_info=None):
    """Setup the calendar platform for event devices."""
    if disc_info is None:
        return

    if not any([data[CONF_TRACK] for data in disc_info[CONF_ENTITIES]]):
        return

    calendar_service = GoogleCalendarService(hass.config.path(TOKEN_FILE))
    add_devices([GoogleCalendarEventDevice(hass, calendar_service,
                                           disc_info[CONF_CAL_ID], data)
                 for data in disc_info[CONF_ENTITIES] if data[CONF_TRACK]])


# pylint: disable=too-many-instance-attributes
class GoogleCalendarEventDevice(CalendarEventDevice):
    """A calendar event device."""

    def __init__(self, hass, calendar_service, calendar, data):
        """Create the Calendar event device."""
        self.data = GoogleCalendarData(calendar_service, calendar,
                                       data.get('search', None))
        super().__init__(hass, data)


class GoogleCalendarData(object):
    """Class to utilize calendar service object to get next event."""

    def __init__(self, calendar_service, calendar_id, search=None):
        """Setup how we are going to search the google calendar."""
        self.calendar_service = calendar_service
        self.calendar_id = calendar_id
        self.search = search
        self.event = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data."""
        service = self.calendar_service.get()
        params = dict(DEFAULT_GOOGLE_SEARCH_PARAMS)
        params['timeMin'] = dt.start_of_local_day().isoformat('T')
        params['calendarId'] = self.calendar_id
        if self.search:
            params['q'] = self.search

        events = service.events()  # pylint: disable=no-member
        result = events.list(**params).execute()

        items = result.get('items', [])
        self.event = items[0] if len(items) == 1 else None
        return True

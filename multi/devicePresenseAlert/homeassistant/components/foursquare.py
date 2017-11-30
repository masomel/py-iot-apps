"""
Allows utilizing the Foursquare (Swarm) API.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/foursquare/
"""
import asyncio
import logging
import os

import requests
import voluptuous as vol

from homeassistant.const import CONF_ACCESS_TOKEN, HTTP_BAD_REQUEST
from homeassistant.config import load_yaml_config_file
import homeassistant.helpers.config_validation as cv
from homeassistant.components.http import HomeAssistantView

_LOGGER = logging.getLogger(__name__)

CONF_PUSH_SECRET = 'push_secret'

DEPENDENCIES = ['http']
DOMAIN = 'foursquare'

EVENT_CHECKIN = 'foursquare.checkin'
EVENT_PUSH = 'foursquare.push'

SERVICE_CHECKIN = 'checkin'

CHECKIN_SERVICE_SCHEMA = vol.Schema({
    vol.Optional('alt'): cv.string,
    vol.Optional('altAcc'): cv.string,
    vol.Optional('broadcast'): cv.string,
    vol.Optional('eventId'): cv.string,
    vol.Optional('ll'): cv.string,
    vol.Optional('llAcc'): cv.string,
    vol.Optional('mentions'): cv.string,
    vol.Optional('shout'): cv.string,
    vol.Required('venueId'): cv.string,
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_ACCESS_TOKEN): cv.string,
        vol.Required(CONF_PUSH_SECRET): cv.string,
    }),
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Setup the Foursquare component."""
    descriptions = load_yaml_config_file(
        os.path.join(os.path.dirname(__file__), 'services.yaml'))

    config = config[DOMAIN]

    def checkin_user(call):
        """Check a user in on Swarm."""
        url = ("https://api.foursquare.com/v2/checkins/add"
               "?oauth_token={}"
               "&v=20160802"
               "&m=swarm").format(config[CONF_ACCESS_TOKEN])
        response = requests.post(url, data=call.data, timeout=10)

        if response.status_code not in (200, 201):
            _LOGGER.exception(
                "Error checking in user. Response %d: %s:",
                response.status_code, response.reason)

        hass.bus.fire(EVENT_CHECKIN, response.text)

    # Register our service with Home Assistant.
    hass.services.register(DOMAIN, 'checkin', checkin_user,
                           descriptions[DOMAIN][SERVICE_CHECKIN],
                           schema=CHECKIN_SERVICE_SCHEMA)

    hass.http.register_view(FoursquarePushReceiver(config[CONF_PUSH_SECRET]))

    return True


class FoursquarePushReceiver(HomeAssistantView):
    """Handle pushes from the Foursquare API."""

    requires_auth = False
    url = "/api/foursquare"
    name = "foursquare"

    def __init__(self, push_secret):
        """Initialize the OAuth callback view."""
        self.push_secret = push_secret

    @asyncio.coroutine
    def post(self, request):
        """Accept the POST from Foursquare."""
        try:
            data = yield from request.json()
        except ValueError:
            return self.json_message('Invalid JSON', HTTP_BAD_REQUEST)

        secret = data.pop('secret', None)

        _LOGGER.debug("Received Foursquare push: %s", data)

        if self.push_secret != secret:
            _LOGGER.error("Received Foursquare push with invalid"
                          "push secret: %s", secret)
            return self.json_message('Incorrect secret', HTTP_BAD_REQUEST)

        request.app['hass'].bus.async_fire(EVENT_PUSH, data)

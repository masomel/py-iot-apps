"""
Support for BloomSky weather station.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/bloomsky/
"""
import logging
from datetime import timedelta

import requests
import voluptuous as vol

from homeassistant.const import CONF_API_KEY
from homeassistant.helpers import discovery
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

BLOOMSKY = None
BLOOMSKY_TYPE = ['camera', 'binary_sensor', 'sensor']

DOMAIN = 'bloomsky'

# The BloomSky only updates every 5-8 minutes as per the API spec so there's
# no point in polling the API more frequently
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=300)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_API_KEY): cv.string,
    }),
}, extra=vol.ALLOW_EXTRA)


# pylint: disable=unused-argument
def setup(hass, config):
    """Setup BloomSky component."""
    api_key = config[DOMAIN][CONF_API_KEY]

    global BLOOMSKY
    try:
        BLOOMSKY = BloomSky(api_key)
    except RuntimeError:
        return False

    for component in BLOOMSKY_TYPE:
        discovery.load_platform(hass, component, DOMAIN, {}, config)

    return True


class BloomSky(object):
    """Handle all communication with the BloomSky API."""

    # API documentation at http://weatherlution.com/bloomsky-api/
    API_URL = 'https://api.bloomsky.com/api/skydata'

    def __init__(self, api_key):
        """Initialize the BookSky."""
        self._api_key = api_key
        self.devices = {}
        _LOGGER.debug("Initial BloomSky device load...")
        self.refresh_devices()

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def refresh_devices(self):
        """Use the API to retrieve a list of devices."""
        _LOGGER.debug("Fetching BloomSky update")
        response = requests.get(self.API_URL,
                                headers={"Authorization": self._api_key},
                                timeout=10)
        if response.status_code == 401:
            raise RuntimeError("Invalid API_KEY")
        elif response.status_code != 200:
            _LOGGER.error("Invalid HTTP response: %s", response.status_code)
            return
        # Create dictionary keyed off of the device unique id
        self.devices.update({
            device['DeviceID']: device for device in response.json()
        })

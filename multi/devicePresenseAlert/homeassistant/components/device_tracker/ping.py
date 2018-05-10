"""
Tracks devices by sending a ICMP ping.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/device_tracker.ping/

device_tracker:
  - platform: ping
    count: 2
    hosts:
      host_one: pc.local
      host_two: 192.168.2.25
"""
import logging
import subprocess
import sys
from datetime import timedelta

import voluptuous as vol

from homeassistant.components.device_tracker import (
    PLATFORM_SCHEMA, DEFAULT_SCAN_INTERVAL)
from homeassistant.helpers.event import track_point_in_utc_time
from homeassistant import util
from homeassistant import const
import homeassistant.helpers.config_validation as cv

DEPENDENCIES = []

_LOGGER = logging.getLogger(__name__)

CONF_PING_COUNT = 'count'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(const.CONF_HOSTS): {cv.string: cv.string},
    vol.Optional(CONF_PING_COUNT, default=1): cv.positive_int,
})


class Host:
    """Host object with ping detection."""

    def __init__(self, ip_address, dev_id, hass, config):
        """Initialize the Host pinger."""
        self.hass = hass
        self.ip_address = ip_address
        self.dev_id = dev_id
        self._count = config[CONF_PING_COUNT]
        if sys.platform == "win32":
            self._ping_cmd = ['ping', '-n 1', '-w 1000', self.ip_address]
        else:
            self._ping_cmd = ['ping', '-n', '-q', '-c1', '-W1',
                              self.ip_address]

    def ping(self):
        """Send ICMP ping and return True if success."""
        pinger = subprocess.Popen(self._ping_cmd, stdout=subprocess.PIPE)
        try:
            pinger.communicate()
            return pinger.returncode == 0
        except subprocess.CalledProcessError:
            return False

    def update(self, see):
        """Update device state by sending one or more ping messages."""
        failed = 0
        while failed < self._count:  # check more times if host in unreachable
            if self.ping():
                see(dev_id=self.dev_id)
                return True
            failed += 1

        _LOGGER.debug("ping KO on ip=%s failed=%d", self.ip_address, failed)


def setup_scanner(hass, config, see):
    """Setup the Host objects and return the update function."""
    hosts = [Host(ip, dev_id, hass, config) for (dev_id, ip) in
             list(config[const.CONF_HOSTS].items())]
    interval = timedelta(seconds=len(hosts) * config[CONF_PING_COUNT] +
                         DEFAULT_SCAN_INTERVAL)
    _LOGGER.info("Started ping tracker with interval=%s on hosts: %s",
                 interval, ",".join([host.ip_address for host in hosts]))

    def update(now):
        """Update all the hosts on every interval time."""
        for host in hosts:
            host.update(see)
        track_point_in_utc_time(hass, update, now + interval)
        return True

    return update(util.dt.utcnow())

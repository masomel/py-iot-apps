"""Ban logic for HTTP component."""
import asyncio
from collections import defaultdict
from datetime import datetime
from ipaddress import ip_address
import logging

from aiohttp.web_exceptions import HTTPForbidden
import voluptuous as vol

from homeassistant.components import persistent_notification
from homeassistant.config import load_yaml_config_file
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv
from homeassistant.util.yaml import dump
from .const import (
    KEY_BANS_ENABLED, KEY_BANNED_IPS, KEY_LOGIN_THRESHOLD,
    KEY_FAILED_LOGIN_ATTEMPTS)
from .util import get_real_ip

NOTIFICATION_ID_BAN = 'ip-ban'

IP_BANS_FILE = 'ip_bans.yaml'
ATTR_BANNED_AT = "banned_at"

SCHEMA_IP_BAN_ENTRY = vol.Schema({
    vol.Optional('banned_at'): vol.Any(None, cv.datetime)
})

_LOGGER = logging.getLogger(__name__)


@asyncio.coroutine
def ban_middleware(app, handler):
    """IP Ban middleware."""
    if not app[KEY_BANS_ENABLED]:
        return handler

    if KEY_BANNED_IPS not in app:
        hass = app['hass']
        app[KEY_BANNED_IPS] = yield from hass.loop.run_in_executor(
            None, load_ip_bans_config, hass.config.path(IP_BANS_FILE))

    @asyncio.coroutine
    def ban_middleware_handler(request):
        """Verify if IP is not banned."""
        ip_address_ = get_real_ip(request)

        is_banned = any(ip_ban.ip_address == ip_address_
                        for ip_ban in request.app[KEY_BANNED_IPS])

        if is_banned:
            raise HTTPForbidden()

        return handler(request)

    return ban_middleware_handler


@asyncio.coroutine
def process_wrong_login(request):
    """Process a wrong login attempt."""
    if (not request.app[KEY_BANS_ENABLED] or
            request.app[KEY_LOGIN_THRESHOLD] < 1):
        return

    if KEY_FAILED_LOGIN_ATTEMPTS not in request.app:
        request.app[KEY_FAILED_LOGIN_ATTEMPTS] = defaultdict(int)

    remote_addr = get_real_ip(request)

    request.app[KEY_FAILED_LOGIN_ATTEMPTS][remote_addr] += 1

    if (request.app[KEY_FAILED_LOGIN_ATTEMPTS][remote_addr] >
            request.app[KEY_LOGIN_THRESHOLD]):
        new_ban = IpBan(remote_addr)
        request.app[KEY_BANNED_IPS].append(new_ban)

        hass = request.app['hass']
        yield from hass.loop.run_in_executor(
            None, update_ip_bans_config, hass.config.path(IP_BANS_FILE),
            new_ban)

        _LOGGER.warning('Banned IP %s for too many login attempts',
                        remote_addr)

        persistent_notification.async_create(
            hass,
            'Too many login attempts from {}'.format(remote_addr),
            'Banning IP address', NOTIFICATION_ID_BAN)


class IpBan(object):
    """Represents banned IP address."""

    def __init__(self, ip_ban: str, banned_at: datetime=None) -> None:
        """Initializing Ip Ban object."""
        self.ip_address = ip_address(ip_ban)
        self.banned_at = banned_at or datetime.utcnow()


def load_ip_bans_config(path: str):
    """Loading list of banned IPs from config file."""
    ip_list = []

    try:
        list_ = load_yaml_config_file(path)
    except FileNotFoundError:
        return []
    except HomeAssistantError as err:
        _LOGGER.error('Unable to load %s: %s', path, str(err))
        return []

    for ip_ban, ip_info in list_.items():
        try:
            ip_info = SCHEMA_IP_BAN_ENTRY(ip_info)
            ip_list.append(IpBan(ip_ban, ip_info['banned_at']))
        except vol.Invalid as err:
            _LOGGER.error('Failed to load IP ban %s: %s', ip_info, err)
            continue

    return ip_list


def update_ip_bans_config(path: str, ip_ban: IpBan):
    """Update config file with new banned IP address."""
    with open(path, 'a') as out:
        ip_ = {str(ip_ban.ip_address): {
            ATTR_BANNED_AT: ip_ban.banned_at.strftime("%Y-%m-%dT%H:%M:%S")
        }}
        out.write('\n')
        out.write(dump(ip_))

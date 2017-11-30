"""
HTML5 Push Messaging notification service.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/notify.html5/
"""
import asyncio
import os
import logging
import json
import time
import datetime
import uuid

import voluptuous as vol
from voluptuous.humanize import humanize_error

from homeassistant.const import (HTTP_BAD_REQUEST, HTTP_INTERNAL_SERVER_ERROR,
                                 HTTP_UNAUTHORIZED, URL_ROOT)
from homeassistant.util import ensure_unique_string
from homeassistant.components.notify import (
    ATTR_TARGET, ATTR_TITLE, ATTR_TITLE_DEFAULT, ATTR_DATA,
    BaseNotificationService, PLATFORM_SCHEMA)
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.frontend import add_manifest_json_key
from homeassistant.helpers import config_validation as cv

REQUIREMENTS = ['pywebpush==0.6.1', 'PyJWT==1.4.2']

DEPENDENCIES = ['frontend']

_LOGGER = logging.getLogger(__name__)

REGISTRATIONS_FILE = 'html5_push_registrations.conf'

ATTR_GCM_SENDER_ID = 'gcm_sender_id'
ATTR_GCM_API_KEY = 'gcm_api_key'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(ATTR_GCM_SENDER_ID): cv.string,
    vol.Optional(ATTR_GCM_API_KEY): cv.string,
})

ATTR_SUBSCRIPTION = 'subscription'
ATTR_BROWSER = 'browser'

ATTR_ENDPOINT = 'endpoint'
ATTR_KEYS = 'keys'
ATTR_AUTH = 'auth'
ATTR_P256DH = 'p256dh'

ATTR_TAG = 'tag'
ATTR_ACTION = 'action'
ATTR_ACTIONS = 'actions'
ATTR_TYPE = 'type'
ATTR_URL = 'url'

ATTR_JWT = 'jwt'

# The number of days after the moment a notification is sent that a JWT
# is valid.
JWT_VALID_DAYS = 7

KEYS_SCHEMA = vol.All(dict,
                      vol.Schema({
                          vol.Required(ATTR_AUTH): cv.string,
                          vol.Required(ATTR_P256DH): cv.string
                          }))

SUBSCRIPTION_SCHEMA = vol.All(dict,
                              vol.Schema({
                                  # pylint: disable=no-value-for-parameter
                                  vol.Required(ATTR_ENDPOINT): vol.Url(),
                                  vol.Required(ATTR_KEYS): KEYS_SCHEMA
                                  }))

REGISTER_SCHEMA = vol.Schema({
    vol.Required(ATTR_SUBSCRIPTION): SUBSCRIPTION_SCHEMA,
    vol.Required(ATTR_BROWSER): vol.In(['chrome', 'firefox'])
})

CALLBACK_EVENT_PAYLOAD_SCHEMA = vol.Schema({
    vol.Required(ATTR_TAG): cv.string,
    vol.Required(ATTR_TYPE): vol.In(['received', 'clicked', 'closed']),
    vol.Required(ATTR_TARGET): cv.string,
    vol.Optional(ATTR_ACTION): cv.string,
    vol.Optional(ATTR_DATA): dict,
})

NOTIFY_CALLBACK_EVENT = 'html5_notification'

# badge and timestamp are Chrome specific (not in official spec)

HTML5_SHOWNOTIFICATION_PARAMETERS = ('actions', 'badge', 'body', 'dir',
                                     'icon', 'lang', 'renotify',
                                     'requireInteraction', 'tag', 'timestamp',
                                     'vibrate')


def get_service(hass, config):
    """Get the HTML5 push notification service."""
    json_path = hass.config.path(REGISTRATIONS_FILE)

    registrations = _load_config(json_path)

    if registrations is None:
        return None

    hass.http.register_view(
        HTML5PushRegistrationView(registrations, json_path))
    hass.http.register_view(HTML5PushCallbackView(registrations))

    gcm_api_key = config.get(ATTR_GCM_API_KEY)
    gcm_sender_id = config.get(ATTR_GCM_SENDER_ID)

    if gcm_sender_id is not None:
        add_manifest_json_key(ATTR_GCM_SENDER_ID,
                              config.get(ATTR_GCM_SENDER_ID))

    return HTML5NotificationService(gcm_api_key, registrations)


def _load_config(filename):
    """Load configuration."""
    if not os.path.isfile(filename):
        return {}

    try:
        with open(filename, 'r') as fdesc:
            inp = fdesc.read()

        # In case empty file
        if not inp:
            return {}

        return json.loads(inp)
    except (IOError, ValueError) as error:
        _LOGGER.error('Reading config file %s failed: %s', filename, error)
        return None


class JSONBytesDecoder(json.JSONEncoder):
    """JSONEncoder to decode bytes objects to unicode."""

    # pylint: disable=method-hidden
    def default(self, obj):
        """Decode object if it's a bytes object, else defer to baseclass."""
        if isinstance(obj, bytes):
            return obj.decode()
        return json.JSONEncoder.default(self, obj)


def _save_config(filename, config):
    """Save configuration."""
    try:
        with open(filename, 'w') as fdesc:
            fdesc.write(json.dumps(
                config, cls=JSONBytesDecoder, indent=4, sort_keys=True))
    except (IOError, TypeError) as error:
        _LOGGER.error('Saving config file failed: %s', error)
        return False
    return True


class HTML5PushRegistrationView(HomeAssistantView):
    """Accepts push registrations from a browser."""

    url = '/api/notify.html5'
    name = 'api:notify.html5'

    def __init__(self, registrations, json_path):
        """Init HTML5PushRegistrationView."""
        self.registrations = registrations
        self.json_path = json_path

    @asyncio.coroutine
    def post(self, request):
        """Accept the POST request for push registrations from a browser."""
        try:
            data = yield from request.json()
        except ValueError:
            return self.json_message('Invalid JSON', HTTP_BAD_REQUEST)

        try:
            data = REGISTER_SCHEMA(data)
        except vol.Invalid as ex:
            return self.json_message(humanize_error(data, ex),
                                     HTTP_BAD_REQUEST)

        name = ensure_unique_string('unnamed device',
                                    self.registrations.keys())

        self.registrations[name] = data

        if not _save_config(self.json_path, self.registrations):
            return self.json_message('Error saving registration.',
                                     HTTP_INTERNAL_SERVER_ERROR)

        return self.json_message('Push notification subscriber registered.')

    @asyncio.coroutine
    def delete(self, request):
        """Delete a registration."""
        try:
            data = yield from request.json()
        except ValueError:
            return self.json_message('Invalid JSON', HTTP_BAD_REQUEST)

        subscription = data.get(ATTR_SUBSCRIPTION)

        found = None

        for key, registration in self.registrations.items():
            if registration.get(ATTR_SUBSCRIPTION) == subscription:
                found = key
                break

        if not found:
            # If not found, unregistering was already done. Return 200
            return self.json_message('Registration not found.')

        reg = self.registrations.pop(found)

        if not _save_config(self.json_path, self.registrations):
            self.registrations[found] = reg
            return self.json_message('Error saving registration.',
                                     HTTP_INTERNAL_SERVER_ERROR)

        return self.json_message('Push notification subscriber unregistered.')


class HTML5PushCallbackView(HomeAssistantView):
    """Accepts push registrations from a browser."""

    requires_auth = False
    url = '/api/notify.html5/callback'
    name = 'api:notify.html5/callback'

    def __init__(self, registrations):
        """Init HTML5PushCallbackView."""
        self.registrations = registrations

    def decode_jwt(self, token):
        """Find the registration that signed this JWT and return it."""
        import jwt

        # 1.  Check claims w/o verifying to see if a target is in there.
        # 2.  If target in claims, attempt to verify against the given name.
        # 2a. If decode is successful, return the payload.
        # 2b. If decode is unsuccessful, return a 401.

        target_check = jwt.decode(token, verify=False)
        if target_check[ATTR_TARGET] in self.registrations:
            possible_target = self.registrations[target_check[ATTR_TARGET]]
            key = possible_target[ATTR_SUBSCRIPTION][ATTR_KEYS][ATTR_AUTH]
            try:
                return jwt.decode(token, key)
            except jwt.exceptions.DecodeError:
                pass

        return self.json_message('No target found in JWT',
                                 status_code=HTTP_UNAUTHORIZED)

    # The following is based on code from Auth0
    # https://auth0.com/docs/quickstart/backend/python
    def check_authorization_header(self, request):
        """Check the authorization header."""
        import jwt
        auth = request.headers.get('Authorization', None)
        if not auth:
            return self.json_message('Authorization header is expected',
                                     status_code=HTTP_UNAUTHORIZED)

        parts = auth.split()

        if parts[0].lower() != 'bearer':
            return self.json_message('Authorization header must '
                                     'start with Bearer',
                                     status_code=HTTP_UNAUTHORIZED)
        elif len(parts) != 2:
            return self.json_message('Authorization header must '
                                     'be Bearer token',
                                     status_code=HTTP_UNAUTHORIZED)

        token = parts[1]
        try:
            payload = self.decode_jwt(token)
        except jwt.exceptions.InvalidTokenError:
            return self.json_message('token is invalid',
                                     status_code=HTTP_UNAUTHORIZED)
        return payload

    @asyncio.coroutine
    def post(self, request):
        """Accept the POST request for push registrations event callback."""
        auth_check = self.check_authorization_header(request)
        if not isinstance(auth_check, dict):
            return auth_check

        try:
            data = yield from request.json()
        except ValueError:
            return self.json_message('Invalid JSON', HTTP_BAD_REQUEST)

        event_payload = {
            ATTR_TAG: data.get(ATTR_TAG),
            ATTR_TYPE: data[ATTR_TYPE],
            ATTR_TARGET: auth_check[ATTR_TARGET],
        }

        if data.get(ATTR_ACTION) is not None:
            event_payload[ATTR_ACTION] = data.get(ATTR_ACTION)

        if data.get(ATTR_DATA) is not None:
            event_payload[ATTR_DATA] = data.get(ATTR_DATA)

        try:
            event_payload = CALLBACK_EVENT_PAYLOAD_SCHEMA(event_payload)
        except vol.Invalid as ex:
            _LOGGER.warning('Callback event payload is not valid! %s',
                            humanize_error(event_payload, ex))

        event_name = '{}.{}'.format(NOTIFY_CALLBACK_EVENT,
                                    event_payload[ATTR_TYPE])
        request.app['hass'].bus.fire(event_name, event_payload)
        return self.json({'status': 'ok',
                          'event': event_payload[ATTR_TYPE]})


class HTML5NotificationService(BaseNotificationService):
    """Implement the notification service for HTML5."""

    def __init__(self, gcm_key, registrations):
        """Initialize the service."""
        self._gcm_key = gcm_key
        self.registrations = registrations

    @property
    def targets(self):
        """Return a dictionary of registered targets."""
        targets = {}
        for registration in self.registrations:
            targets[registration] = registration
        return targets

    def send_message(self, message="", **kwargs):
        """Send a message to a user."""
        import jwt
        from pywebpush import WebPusher

        timestamp = int(time.time())
        tag = str(uuid.uuid4())

        payload = {
            'badge': '/static/images/notification-badge.png',
            'body': message,
            ATTR_DATA: {},
            'icon': '/static/icons/favicon-192x192.png',
            ATTR_TAG: tag,
            'timestamp': (timestamp*1000),  # Javascript ms since epoch
            ATTR_TITLE: kwargs.get(ATTR_TITLE, ATTR_TITLE_DEFAULT)
        }

        data = kwargs.get(ATTR_DATA)

        if data:
            # Pick out fields that should go into the notification directly vs
            # into the notification data dictionary.

            data_tmp = {}

            for key, val in data.items():
                if key in HTML5_SHOWNOTIFICATION_PARAMETERS:
                    payload[key] = val
                else:
                    data_tmp[key] = val

            payload[ATTR_DATA] = data_tmp

        if (payload[ATTR_DATA].get(ATTR_URL) is None and
                payload.get(ATTR_ACTIONS) is None):
            payload[ATTR_DATA][ATTR_URL] = URL_ROOT

        targets = kwargs.get(ATTR_TARGET)

        if not targets:
            targets = self.registrations.keys()

        for target in targets:
            info = self.registrations.get(target)
            if info is None:
                _LOGGER.error('%s is not a valid HTML5 push notification'
                              ' target!', target)
                continue

            jwt_exp = (datetime.datetime.fromtimestamp(timestamp) +
                       datetime.timedelta(days=JWT_VALID_DAYS))
            jwt_secret = info[ATTR_SUBSCRIPTION][ATTR_KEYS][ATTR_AUTH]
            jwt_claims = {'exp': jwt_exp, 'nbf': timestamp,
                          'iat': timestamp, ATTR_TARGET: target,
                          ATTR_TAG: payload[ATTR_TAG]}
            jwt_token = jwt.encode(jwt_claims, jwt_secret).decode('utf-8')
            payload[ATTR_DATA][ATTR_JWT] = jwt_token

            WebPusher(info[ATTR_SUBSCRIPTION]).send(
                json.dumps(payload), gcm_key=self._gcm_key, ttl='86400')

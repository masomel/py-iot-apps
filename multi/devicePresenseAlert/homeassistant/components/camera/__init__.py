# pylint: disable=too-many-lines
"""
Component to interface with cameras.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/camera/
"""
import asyncio
from datetime import timedelta
import logging
import hashlib

from aiohttp import web

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA  # noqa
from homeassistant.components.http import HomeAssistantView, KEY_AUTHENTICATED

DOMAIN = 'camera'
DEPENDENCIES = ['http']
SCAN_INTERVAL = timedelta(seconds=30)
ENTITY_ID_FORMAT = DOMAIN + '.{}'

STATE_RECORDING = 'recording'
STATE_STREAMING = 'streaming'
STATE_IDLE = 'idle'

ENTITY_IMAGE_URL = '/api/camera_proxy/{0}?token={1}'


@asyncio.coroutine
def async_setup(hass, config):
    """Setup the camera component."""
    component = EntityComponent(
        logging.getLogger(__name__), DOMAIN, hass, SCAN_INTERVAL)

    hass.http.register_view(CameraImageView(component.entities))
    hass.http.register_view(CameraMjpegStream(component.entities))

    yield from component.async_setup(config)
    return True


class Camera(Entity):
    """The base class for camera entities."""

    def __init__(self):
        """Initialize a camera."""
        self.is_streaming = False
        self._access_token = hashlib.sha256(
            str.encode(str(id(self)))).hexdigest()

    @property
    def access_token(self):
        """Access token for this camera."""
        return self._access_token

    @property
    def should_poll(self):
        """No need to poll cameras."""
        return False

    @property
    def entity_picture(self):
        """Return a link to the camera feed as entity picture."""
        return ENTITY_IMAGE_URL.format(self.entity_id, self.access_token)

    @property
    def is_recording(self):
        """Return true if the device is recording."""
        return False

    @property
    def brand(self):
        """Camera brand."""
        return None

    @property
    def model(self):
        """Camera model."""
        return None

    def camera_image(self):
        """Return bytes of camera image."""
        raise NotImplementedError()

    def async_camera_image(self):
        """Return bytes of camera image.

        This method must be run in the event loop and returns a coroutine.
        """
        return self.hass.loop.run_in_executor(None, self.camera_image)

    @asyncio.coroutine
    def handle_async_mjpeg_stream(self, request):
        """Generate an HTTP MJPEG stream from camera images.

        This method must be run in the event loop.
        """
        response = web.StreamResponse()

        response.content_type = ('multipart/x-mixed-replace; '
                                 'boundary=--jpegboundary')
        yield from response.prepare(request)

        def write(img_bytes):
            """Write image to stream."""
            response.write(bytes(
                '--jpegboundary\r\n'
                'Content-Type: image/jpeg\r\n'
                'Content-Length: {}\r\n\r\n'.format(
                    len(img_bytes)), 'utf-8') + img_bytes + b'\r\n')

        last_image = None

        try:
            while True:
                img_bytes = yield from self.async_camera_image()
                if not img_bytes:
                    break

                if img_bytes is not None and img_bytes != last_image:
                    write(img_bytes)

                    # Chrome seems to always ignore first picture,
                    # print it twice.
                    if last_image is None:
                        write(img_bytes)

                    last_image = img_bytes
                    yield from response.drain()

                yield from asyncio.sleep(.5)
        finally:
            yield from response.write_eof()

    @property
    def state(self):
        """Camera state."""
        if self.is_recording:
            return STATE_RECORDING
        elif self.is_streaming:
            return STATE_STREAMING
        else:
            return STATE_IDLE

    @property
    def state_attributes(self):
        """Camera state attributes."""
        attr = {
            'access_token': self.access_token,
        }

        if self.model:
            attr['model_name'] = self.model

        if self.brand:
            attr['brand'] = self.brand

        return attr


class CameraView(HomeAssistantView):
    """Base CameraView."""

    requires_auth = False

    def __init__(self, entities):
        """Initialize a basic camera view."""
        self.entities = entities

    @asyncio.coroutine
    def get(self, request, entity_id):
        """Start a get request."""
        camera = self.entities.get(entity_id)

        if camera is None:
            return web.Response(status=404)

        authenticated = (request[KEY_AUTHENTICATED] or
                         request.GET.get('token') == camera.access_token)

        if not authenticated:
            return web.Response(status=401)

        response = yield from self.handle(request, camera)
        return response

    @asyncio.coroutine
    def handle(self, request, camera):
        """Hanlde the camera request."""
        raise NotImplementedError()


class CameraImageView(CameraView):
    """Camera view to serve an image."""

    url = "/api/camera_proxy/{entity_id}"
    name = "api:camera:image"

    @asyncio.coroutine
    def handle(self, request, camera):
        """Serve camera image."""
        image = yield from camera.async_camera_image()

        if image is None:
            return web.Response(status=500)

        return web.Response(body=image)


class CameraMjpegStream(CameraView):
    """Camera View to serve an MJPEG stream."""

    url = "/api/camera_proxy_stream/{entity_id}"
    name = "api:camera:stream"

    @asyncio.coroutine
    def handle(self, request, camera):
        """Serve camera image."""
        yield from camera.handle_async_mjpeg_stream(request)

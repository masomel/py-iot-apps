"""
Support for the demo speech service.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/demo/
"""
import os

import voluptuous as vol

from homeassistant.components.tts import Provider, PLATFORM_SCHEMA, CONF_LANG

SUPPORT_LANGUAGES = [
    'en', 'de'
]

DEFAULT_LANG = 'en'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_LANG, default=DEFAULT_LANG): vol.In(SUPPORT_LANGUAGES),
})


def get_engine(hass, config):
    """Setup Demo speech component."""
    return DemoProvider(config[CONF_LANG])


class DemoProvider(Provider):
    """Demo speech api provider."""

    def __init__(self, lang):
        """Initialize demo provider."""
        self._lang = lang

    @property
    def default_language(self):
        """Default language."""
        return self._lang

    @property
    def supported_languages(self):
        """List of supported languages."""
        return SUPPORT_LANGUAGES

    def get_tts_audio(self, message, language):
        """Load TTS from demo."""
        filename = os.path.join(os.path.dirname(__file__), "demo.mp3")
        try:
            with open(filename, 'rb') as voice:
                data = voice.read()
        except OSError:
            return (None, None)

        return ("mp3", data)

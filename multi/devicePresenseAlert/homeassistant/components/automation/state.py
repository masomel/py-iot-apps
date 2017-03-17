"""
Offer state listening automation rules.

For more details about this automation rule, please refer to the documentation
at https://home-assistant.io/components/automation/#state-trigger
"""
import voluptuous as vol

from homeassistant.core import callback
import homeassistant.util.dt as dt_util
from homeassistant.const import MATCH_ALL, CONF_PLATFORM
from homeassistant.helpers.event import (
    async_track_state_change, async_track_point_in_utc_time)
import homeassistant.helpers.config_validation as cv

CONF_ENTITY_ID = "entity_id"
CONF_FROM = "from"
CONF_TO = "to"
CONF_STATE = "state"
CONF_FOR = "for"

TRIGGER_SCHEMA = vol.All(
    vol.Schema({
        vol.Required(CONF_PLATFORM): 'state',
        vol.Required(CONF_ENTITY_ID): cv.entity_ids,
        # These are str on purpose. Want to catch YAML conversions
        CONF_FROM: str,
        CONF_TO: str,
        CONF_STATE: str,
        CONF_FOR: vol.All(cv.time_period, cv.positive_timedelta),
    }),
    vol.Any(cv.key_dependency(CONF_FOR, CONF_TO),
            cv.key_dependency(CONF_FOR, CONF_STATE))
)


def async_trigger(hass, config, action):
    """Listen for state changes based on configuration."""
    entity_id = config.get(CONF_ENTITY_ID)
    from_state = config.get(CONF_FROM, MATCH_ALL)
    to_state = config.get(CONF_TO) or config.get(CONF_STATE) or MATCH_ALL
    time_delta = config.get(CONF_FOR)
    async_remove_state_for_cancel = None
    async_remove_state_for_listener = None

    @callback
    def state_automation_listener(entity, from_s, to_s):
        """Listen for state changes and calls action."""
        nonlocal async_remove_state_for_cancel, async_remove_state_for_listener

        def call_action():
            """Call action with right context."""
            hass.async_run_job(action, {
                'trigger': {
                    'platform': 'state',
                    'entity_id': entity,
                    'from_state': from_s,
                    'to_state': to_s,
                    'for': time_delta,
                }
            })

        if time_delta is None:
            call_action()
            return

        @callback
        def clear_listener():
            """Clear all unsub listener."""
            nonlocal async_remove_state_for_cancel
            nonlocal async_remove_state_for_listener
            async_remove_state_for_listener = None
            async_remove_state_for_cancel = None

        @callback
        def state_for_listener(now):
            """Fire on state changes after a delay and calls action."""
            async_remove_state_for_cancel()
            clear_listener()
            call_action()

        @callback
        def state_for_cancel_listener(entity, inner_from_s, inner_to_s):
            """Fire on changes and cancel for listener if changed."""
            if inner_to_s.state == to_s.state:
                return
            async_remove_state_for_listener()
            async_remove_state_for_cancel()
            clear_listener()

        async_remove_state_for_listener = async_track_point_in_utc_time(
            hass, state_for_listener, dt_util.utcnow() + time_delta)

        async_remove_state_for_cancel = async_track_state_change(
            hass, entity, state_for_cancel_listener)

    unsub = async_track_state_change(
        hass, entity_id, state_automation_listener, from_state, to_state)

    def async_remove():
        """Remove state listeners async."""
        unsub()
        # pylint: disable=not-callable
        if async_remove_state_for_cancel is not None:
            async_remove_state_for_cancel()

        if async_remove_state_for_listener is not None:
            async_remove_state_for_listener()

    return async_remove

"""
AWS SNS platform for notify component.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/notify.aws_sns/
"""
import logging
import json

import voluptuous as vol

from homeassistant.const import (
    CONF_PLATFORM, CONF_NAME)
from homeassistant.components.notify import (
    ATTR_TITLE, ATTR_TITLE_DEFAULT, ATTR_TARGET, PLATFORM_SCHEMA,
    BaseNotificationService)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)
REQUIREMENTS = ["boto3==1.3.1"]

CONF_REGION = 'region_name'
CONF_ACCESS_KEY_ID = 'aws_access_key_id'
CONF_SECRET_ACCESS_KEY = 'aws_secret_access_key'
CONF_PROFILE_NAME = 'profile_name'
ATTR_CREDENTIALS = 'credentials'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_REGION, default="us-east-1"): cv.string,
    vol.Inclusive(CONF_ACCESS_KEY_ID, ATTR_CREDENTIALS): cv.string,
    vol.Inclusive(CONF_SECRET_ACCESS_KEY, ATTR_CREDENTIALS): cv.string,
    vol.Exclusive(CONF_PROFILE_NAME, ATTR_CREDENTIALS): cv.string,
})


def get_service(hass, config):
    """Get the AWS SNS notification service."""
    # pylint: disable=import-error
    import boto3

    aws_config = config.copy()

    del aws_config[CONF_PLATFORM]
    del aws_config[CONF_NAME]

    profile = aws_config.get(CONF_PROFILE_NAME)

    if profile is not None:
        boto3.setup_default_session(profile_name=profile)
        del aws_config[CONF_PROFILE_NAME]

    sns_client = boto3.client("sns", **aws_config)

    return AWSSNS(sns_client)


class AWSSNS(BaseNotificationService):
    """Implement the notification service for the AWS SNS service."""

    def __init__(self, sns_client):
        """Initialize the service."""
        self.client = sns_client

    def send_message(self, message="", **kwargs):
        """Send notification to specified SNS ARN."""
        targets = kwargs.get(ATTR_TARGET)

        if not targets:
            _LOGGER.info("At least 1 target is required")
            return

        message_attributes = {k: {"StringValue": json.dumps(v),
                                  "DataType": "String"}
                              for k, v in list(kwargs.items()) if v}
        for target in targets:
            self.client.publish(TargetArn=target, Message=message,
                                Subject=kwargs.get(ATTR_TITLE,
                                                   ATTR_TITLE_DEFAULT),
                                MessageAttributes=message_attributes)

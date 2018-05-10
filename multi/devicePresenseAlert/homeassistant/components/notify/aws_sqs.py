"""
AWS SQS platform for notify component.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/notify.aws_sqs/
"""
import logging
import json

import voluptuous as vol

from homeassistant.const import (
    CONF_PLATFORM, CONF_NAME)
from homeassistant.components.notify import (
    ATTR_TARGET, PLATFORM_SCHEMA, BaseNotificationService)
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
    """Get the AWS SQS notification service."""
    # pylint: disable=import-error
    import boto3

    aws_config = config.copy()

    del aws_config[CONF_PLATFORM]
    del aws_config[CONF_NAME]

    profile = aws_config.get(CONF_PROFILE_NAME)

    if profile is not None:
        boto3.setup_default_session(profile_name=profile)
        del aws_config[CONF_PROFILE_NAME]

    sqs_client = boto3.client("sqs", **aws_config)

    return AWSSQS(sqs_client)


class AWSSQS(BaseNotificationService):
    """Implement the notification service for the AWS SQS service."""

    def __init__(self, sqs_client):
        """Initialize the service."""
        self.client = sqs_client

    def send_message(self, message="", **kwargs):
        """Send notification to specified SQS ARN."""
        targets = kwargs.get(ATTR_TARGET)

        if not targets:
            _LOGGER.info("At least 1 target is required")
            return

        for target in targets:
            cleaned_kwargs = dict((k, v) for k, v in list(kwargs.items()) if v)
            message_body = {"message": message}
            message_body.update(cleaned_kwargs)
            message_attributes = {}
            for key, val in list(cleaned_kwargs.items()):
                message_attributes[key] = {"StringValue": json.dumps(val),
                                           "DataType": "String"}
            self.client.send_message(QueueUrl=target,
                                     MessageBody=json.dumps(message_body),
                                     MessageAttributes=message_attributes)

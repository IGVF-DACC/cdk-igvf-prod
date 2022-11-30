from aws_cdk import SecretValue

from constructs import Construct

from aws_cdk.aws_events import Rule
from aws_cdk.aws_events import RuleTargetInput
from aws_cdk.aws_events import EventPattern
from aws_cdk.aws_events import Connection
from aws_cdk.aws_events import Authorization
from aws_cdk.aws_events import ApiDestination

from aws_cdk.aws_events_targets import ApiDestination as ApiDestinationToTarget

from aws_cdk.aws_ssm import StringParameter

from dataclasses import dataclass

from typing import Any


class SlackWebhook(Construct):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # Connection needs authorization but this isn't actually used.
        authorization = Authorization.basic(
            'abc',
            SecretValue.unsafe_plain_text('123'),
        )
        connection = Connection(
            self,
            'Connection',
            authorization=authorization,
        )
        # Reference existing SSM parameter with secret URL.
        endpoint = StringParameter.from_string_parameter_name(
            self,
            'SlackWebhookUrl',
            string_parameter_name='SLACK_WEBHOOK_URL_FOR_AWS_IGVF_PROD_CHANNEL'
        )
        api_destination = ApiDestination(
            self,
            'SlackIncomingWebhookDestination',
            connection=connection,
            endpoint=endpoint.string_value,
        )
        # $.detail.data.slack value from event is posted to Slack webhook if
        # $.detail.metadata.includes_slack_notification is True.
        target = ApiDestinationToTarget(
            api_destination=api_destination,
            event=RuleTargetInput.from_event_path(
                '$.detail.data.slack'
            )
        )
        rule = Rule(
            self,
            'PassEventsToSlack',
            event_pattern=EventPattern(
                detail={
                    'metadata': {
                        'includes_slack_notification': [True]
                    }
                }
            ),
            targets=[
                target
            ]
        )

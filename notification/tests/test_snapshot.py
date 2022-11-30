import pytest
import json

from aws_cdk import App
from aws_cdk import Environment

from aws_cdk.assertions import Template


ENVIRONMENT = Environment(
    account='testing',
    region='testing'
)


def test_match_with_snapshot(snapshot):
    from notification.notification_stack import NotificationStack
    app = App()
    stack = NotificationStack(
        app,
        'NotificationStack',
        env=ENVIRONMENT
    )
    template = Template.from_stack(stack)
    snapshot.assert_match(
        json.dumps(
            template.to_json(),
            indent=4,
            sort_keys=True
        ),
        'notification_stack_template.json'
    )

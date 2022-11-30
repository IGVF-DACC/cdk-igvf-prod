#!/usr/bin/env python3
import os

import aws_cdk as cdk

from notification.notification_stack import NotificationStack
from notification.config import config


ENVIRONMENT = cdk.Environment(
    account=config['account'],
    region=config['region'],
)

app = cdk.App()

NotificationStack(
    app,
    'NotificationStack',
    env=ENVIRONMENT,
    termination_protection=True,
)

app.synth()

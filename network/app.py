#!/usr/bin/env python3
import os

from aws_cdk import App
from aws_cdk import Environment

from network.network_stack import NetworkStack
from network.config import config


ENVIRONMENT = Environment(
    account=config['account'],
    region=config['region'],
)

app = App()

NetworkStack(
    app,
    'NetworkStack',
    env=ENVIRONMENT,
    termination_protection=True,
)

app.synth()

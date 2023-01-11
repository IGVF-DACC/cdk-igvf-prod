from aws_cdk import App
from aws_cdk import Environment

from bucket.config import config

from bucket.bucket_stack import BucketStorage


ENVIRONMENT = Environment(
    account=config['account'],
    region=config['region'],
)

app = App()

BucketStorage(
    app,
    'BucketStorage',
    env=ENVIRONMENT,
    termination_protection=True,
)

app.synth()

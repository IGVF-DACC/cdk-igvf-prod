from aws_cdk import App
from aws_cdk import Environment

from bucket.config import config

from bucket.bucket_storage import BucketStorage
from bucket.bucket_access_policies import BucketAccessPolicies


ENVIRONMENT = Environment(
    account=config['account'],
    region=config['region'],
)

app = App()

bucket_storage = BucketStorage(
    app,
    'BucketStorage',
    env=ENVIRONMENT,
    termination_protection=True,
)

bucket_access_polices = BucketAccessPolicies(
    app,
    'BucketAccessPolicies',
    bucket_storage=bucket_storage,
    env=ENVIRONMENT,
    termination_protection=True,
)

app.synth()

from aws_cdk import App
from aws_cdk import Environment

from bucket.config import config

from bucket.bucket_storage import RestrictedBucketStorage
from bucket.bucket_access_policies import RestrictedBucketAccessPolicies


ENVIRONMENT = Environment(
    account=config['account'],
    region=config['region'],
)

app = App()

restricted_bucket_storage = RestrictedBucketStorage(
    app,
    'RestrictedBucketStorage',
    env=ENVIRONMENT,
    termination_protection=True,
)

restricted_bucket_access_polices = RestrictedBucketAccessPolicies(
    app,
    'RestrictedBucketAccessPolicies',
    bucket_storage=restricted_bucket_storage,
    env=ENVIRONMENT,
    termination_protection=True,
)

app.synth()

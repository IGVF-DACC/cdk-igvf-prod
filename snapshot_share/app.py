import json

from aws_cdk import App
from aws_cdk import Environment

from snapshot_share.stacks.snapshot import CopySnapshotStepFunction


IGVF_PROD_ENV = Environment(
    account='035226225042',
    region='us-west-2'
)

DATABASE_IDENTIFIER = 'ipbe3yif4qeg11'

# gotta serialize as string to pass to lambda as env
# igvf-dev, igvf-sandbox/igvf-staging
ACCOUNTS = ['109189702753', '920073238245']

SHARE_TO_ACCOUNTS = json.dumps({'accounts': ACCOUNTS})


app = App()

CopySnapshotStepFunction(
    app,
    'CopySnapshotStepFunction',
    db_identifier=DATABASE_IDENTIFIER,
    share_to_accounts=SHARE_TO_ACCOUNTS,
    env=IGVF_PROD_ENV,
)


app.synth()

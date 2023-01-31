import json

from aws_cdk import App
from aws_cdk import Environment

from snapshot_share.stacks.snapshot import CopySnapshotStepFunction
from snapshot_share.config import config

IGVF_PROD_ENV = Environment(
    account=config['account'],
    region=config['region']
)

DATABASE_IDENTIFIER = config['db_identifier']

ACCOUNTS = config['accounts']

# serialize as string to pass to lambda as env
SHARE_TO_ACCOUNTS = json.dumps({'accounts': ACCOUNTS})


app = App()

CopySnapshotStepFunction(
    app,
    'CopySnapshotStepFunction',
    db_identifier=DATABASE_IDENTIFIER,
    share_to_accounts=SHARE_TO_ACCOUNTS,
    env=ENVIRONMENT,
)


app.synth()

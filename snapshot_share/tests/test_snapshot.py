import pytest

import json

from aws_cdk import Environment


ENVIRONMENT = Environment(
    account='testing',
    region='testing'
)

DATABASE_IDENTIFIER = 'rds-xyz-123'
SHARE_TO_ACCOUNTS = json.dumps({'accounts': ['123456']})


def test_match_with_snapshot(snapshot):
    from aws_cdk import App
    from snapshot_share.stacks.snapshot import CopySnapshotStepFunction
    from aws_cdk.assertions import Template
    app = App()
    stack = CopySnapshotStepFunction(
        app,
        'CopySnapshotStepFunction',
        db_identifier=DATABASE_IDENTIFIER,
        share_to_accounts=SHARE_TO_ACCOUNTS,
        env=ENVIRONMENT,
    )
    template = Template.from_stack(stack)
    snapshot.assert_match(
        json.dumps(
            template.to_json(),
            indent=4,
            sort_keys=True
        ),
        'copy_snapshot_template.json'
    )

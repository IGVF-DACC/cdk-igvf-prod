import pytest
import json

from aws_cdk import App
from aws_cdk import Environment

from aws_cdk.assertions import Template


ENVIRONMENT = Environment(
    account='testing',
    region='testing'
)


def test_igvf_file_transfer_matches_snapshot(snapshot):
    from transfer.igvf import IGVFFileTransferStack
    app = App()
    ift = IGVFFileTransferStack(
        app,
        'IGVFFileTransferStack',
        env=ENVIRONMENT,
    )
    template = Template.from_stack(
        ift
    )
    snapshot.assert_match(
        json.dumps(
            template.to_json(),
            indent=4,
            sort_keys=True
        ),
        'igvf_file_transfer_stack.json'
    )

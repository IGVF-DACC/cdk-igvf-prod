import pytest
import json

from aws_cdk import App
from aws_cdk import Environment

from aws_cdk.assertions import Template


ENVIRONMENT = Environment(
    account='testing',
    region='testing'
)


def test_doi_minting_matches_snapshot(snapshot):
    from doi.doi_minting import DoiMintingStack
    app = App()
    doi_minting = DoiMintingStack(
        app,
        'DoiMintingStack',
        env=ENVIRONMENT
    )
    template = Template.from_stack(doi_minting)
    snapshot.assert_match(
        json.dumps(
            template.to_json(),
            indent=4,
            sort_keys=True
        ),
        'doi_minting_stack.json'
    )

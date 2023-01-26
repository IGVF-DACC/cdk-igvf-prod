import boto3
import json
import logging
import os
import re



logging.basicConfig(
    level=logging.INFO,
    force=True
)


def get_share_to_accounts() -> str:
    accounts = os.getenv('SHARE_TO_ACCOUNTS')
    print(accounts)
    return json.loads(accounts)['accounts']

def get_rds_client():
    return boto3.client('rds')

def share_snapshot_to_accounts(accounts: list,
                               snapshot_id: str,
    ) -> None:
    client = get_rds_client()
    response = client.modify_db_snapshot_attribute(
        DBSnapshotIdentifier=snapshot_id,
        AttributeName='restore',
        ValuesToAdd=accounts)

def strip_snapshot_id(snapshot_id: str) -> str:
    return re.sub('^rds\:', '', snapshot_id)

def share_snapshot(event, context):
    latest_rds_snapshot_id = event['copy_latest_rds_snapshot']
    shareable_id = strip_snapshot_id(latest_rds_snapshot_id)
    logging.info(f'Sharing snapshot: {shareable_id}')
    share_snapshot_to_accounts(
        accounts=get_share_to_accounts(),
        snapshot_id=shareable_id,
    )
    return shareable_id


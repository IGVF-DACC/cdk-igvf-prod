import boto3
import json
import os
import re

import logging

logging.basicConfig(
    level=logging.INFO,
    force=True
)

def get_database_identifier():
    return os.environ['DATABASE_IDENTIFIER']

def get_rds_client():
    return boto3.client('rds')

def get_describe_db_snapshots_paginator(client):
    return client.get_paginator('describe_db_snapshots')

def make_query(paginator, **kwargs):
    return paginator.paginate(**kwargs)

def get_results(query):
    for result in query:
        for snapshot in result['DBSnapshots']:
            yield snapshot


def sort_results_by_create_time(results):
    return sorted(
        results,
        key=lambda result: result['SnapshotCreateTime'],
        reverse=True
    )

def make_target_snapshot_id(source_snapshot_id):
    #for manual snapshots the rds: prefix is not allowed
    target_snapshot_id = re.sub('^rds\:', '', source_snapshot_id)
    return target_snapshot_id

def make_copy_of_rds_snapshot(source_snapshot_id, client):
    response = client.copy_db_snapshot(
                    SourceDBSnapshotIdentifier=source_snapshot_id,
                    TargetDBSnapshotIdentifier=make_target_snapshot_id(source_snapshot_id),
                    Tags=[
                        {
                            'Key': 'copy_of',
                            'Value': source_snapshot_id
                        },
                    ]
               )
    return response

def get_latest_result(sorted_results):
    return list(sorted_results)[0]

def copy_latest_rds_snapshot(event, context):
    db_instance_identifier = get_database_identifier()
    client = get_rds_client()
    paginator = get_describe_db_snapshots_paginator(client)
    query = make_query(
        paginator,
        DBInstanceIdentifier=db_instance_identifier,
    )
    results = get_results(query)
    sorted_results = sort_results_by_create_time(
        results
    )
    latest_result = get_latest_result(sorted_results)
    latest_snapshot_id = latest_result['DBSnapshotIdentifier']
    logging.info(f'Making a copy of snapshot: {latest_snapshot_id}')
    response = make_copy_of_rds_snapshot(latest_snapshot_id, client)
    #serialize datetime objects to string
    response_string = json.loads(
        json.dumps(
            response,
            default=str,
        )
    )
    logging.info(response_string)
    return latest_snapshot_id

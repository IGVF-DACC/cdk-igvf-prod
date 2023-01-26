import json
import os

from aws_cdk import App
from aws_cdk import Duration
from aws_cdk import Environment
from aws_cdk import Stack

from aws_cdk.aws_lambda_python_alpha import PythonFunction
from aws_cdk.aws_lambda import Runtime

from aws_cdk.aws_iam import PolicyStatement
from aws_cdk.aws_iam import Role

from constructs import Construct

from aws_cdk.aws_stepfunctions import JsonPath
from aws_cdk.aws_stepfunctions import Pass
from aws_cdk.aws_stepfunctions import Succeed
from aws_cdk.aws_stepfunctions import StateMachine
from aws_cdk.aws_stepfunctions import TaskInput
from aws_cdk.aws_stepfunctions import Wait
from aws_cdk.aws_stepfunctions import WaitTime
from aws_cdk.aws_stepfunctions import Fail

from aws_cdk.aws_stepfunctions_tasks import LambdaInvoke
from aws_cdk.aws_stepfunctions_tasks import EventBridgePutEvents
from aws_cdk.aws_stepfunctions_tasks import EventBridgePutEventsEntry

from typing import Any

IGVF_DEV_ENV = Environment(account='109189702753', region='us-west-2')
DATABASE_IDENTIFIER = 'ipbe3yif4qeg11'
#gotta serialize as string to pass to lambda as env
SHARE_TO_ACCOUNTS = json.dumps(
    {
        'accounts': ['618537831167']
    }
)
class CopySnapshotStepFunction(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        make_success_message = Pass(
            self,
            'MakeSuccessMessage',
            parameters={
                'detailType': 'SnapShotCompleted',
                'source': 'cdk-igvf-dev.snapshot-share.SnapshotStateMachine',
                'detail': {
                    'metadata': {
                        'includes_slack_notification': True
                    },
                    'data': {
                        'slack': {
                            'text': JsonPath.format(
                                ':white_check_mark: *SnapshotSucceeded* | {}',
                                JsonPath.string_at('$.shared_snapshot_id')
                            )
                        }
                    }
                }
            },
        )

        make_failure_message = Pass(
            self,
            'MakeFailureMessage',
            parameters={
                'detailType': 'SnapShotFailed',
                'source': 'cdk-igvf-dev.snapshot-share.SnapshotStateMachine',
                'detail': {
                    'metadata': {
                        'includes_slack_notification': True
                    },
                    'data': {
                        'slack': {
                            'text': JsonPath.format(
                                ':x: *SnapshotFailed* | {}',
                                DATABASE_IDENTIFIER
                            )
                        }
                    }
                }
            },
        )

        send_slack_notification = EventBridgePutEvents(
            self,
            'SendSlackNotification',
            entries=[
                EventBridgePutEventsEntry(
                    detail_type=JsonPath.string_at('$.detailType'),
                    detail=TaskInput.from_json_path_at('$.detail'),
                    source=JsonPath.string_at('$.source')
                )
            ],
            result_path=JsonPath.DISCARD,
        )

        succeed = Succeed(self, 'Succeed')

        copy_latest_snapshot_lambda = PythonFunction(
            self,
            'MakeLatestSnapshotCopyLambda',
            entry='snapshot_share/lambdas/copy_snapshot',
            runtime=Runtime.PYTHON_3_9,
            index='main.py',
            handler='copy_latest_rds_snapshot',
            timeout=Duration.seconds(60),
            environment={'DATABASE_IDENTIFIER': DATABASE_IDENTIFIER},
        )

        copy_latest_snapshot_lambda.add_to_role_policy(
            PolicyStatement(
                actions=[
                    'rds:DescribeDBSnapshots',
                    'rds:CopyDBSnapshot',
                    'rds:AddTagsToResource'
                ],
                resources=['*'],
            )
        )

        make_copy_of_latest_snapshot = LambdaInvoke(
            self,
            'MakeCopyOfLatestSnapshot',
            lambda_function=copy_latest_snapshot_lambda,
            payload_response_only=True,
            result_selector={
                'copy_latest_rds_snapshot.$': '$'
            }
        )

        share_snapshot_lambda = PythonFunction(
            self,
            'ShareSnapshotCopyLambda',
            entry='snapshot_share/lambdas/share_snapshot',
            runtime=Runtime.PYTHON_3_9,
            index='main.py',
            handler='share_snapshot',
            timeout=Duration.seconds(60),
            environment={'SHARE_TO_ACCOUNTS': SHARE_TO_ACCOUNTS},
        )

        share_snapshot_lambda.add_to_role_policy(
            PolicyStatement(
                actions=[
                    'rds:ModifyDBSnapshotAttribute'
                ],
                resources=['*'],
            )
        )

        share_failed = Fail(self,
            'ShareFailed',
            cause='Snapshot retry limit reached',
        )

        share_failed_procedure = make_failure_message.next(
            send_slack_notification
        )

        share_snapshot = LambdaInvoke(
            self,
            'ShareLatestSnapshot',
            lambda_function=share_snapshot_lambda,
            payload_response_only=True,
            result_selector={
                'shared_snapshot_id.$': '$'
            }
        )

        share_snapshot.add_retry(
            backoff_rate=2,
            errors=['InvalidDBSnapshotStateFault'],
            interval=Duration.seconds(1),
            max_attempts=4,
        )

        share_snapshot.add_catch(share_failed_procedure)

        wait_ten_minutes = Wait(
            self,
            'WaitTenMinutes',
            time=WaitTime.duration(
                Duration.seconds(10)
            )
        )

        definition = make_copy_of_latest_snapshot.next(
            wait_ten_minutes
        ).next(
            share_snapshot
        ).next(
            make_success_message
        ).next(
            send_slack_notification
        )

        state_machine = StateMachine(
            self,
            'StateMachine',
            definition=definition
        )

app = App()

copy_snapshot_stepfunction = CopySnapshotStepFunction(app, 'CopySnapshotStepFunction', env=IGVF_DEV_ENV)

app.synth()

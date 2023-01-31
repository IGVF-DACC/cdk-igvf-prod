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


class CopySnapshotStepFunction(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            db_identifier: str,
            share_to_accounts: str,
            **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.db_identifier = db_identifier
        self.share_to_accounts = share_to_accounts

        make_snapshot_copy_failure_message = Pass(
            self,
            'MakeSnapshotCopyFailureMessage',
            parameters={
                'detailType': 'SnapShotCopyFailed',
                'source': 'cdk-igvf-prod.snapshot-share.SnapshotStateMachine',
                'detail': {
                    'metadata': {
                        'includes_slack_notification': True
                    },
                    'data': {
                        'slack': {
                            'text': JsonPath.format(
                                ':x: *SnapshotCopyFailed* | Database ID: {}',
                                self.db_identifier
                            )
                        }
                    }
                }
            },
        )

        make_snapshot_share_success_message = Pass(
            self,
            'MakeSnapshotShareSuccessMessage',
            parameters={
                'detailType': 'SnapShotShareCompleted',
                'source': 'cdk-igvf-prod.snapshot-share.SnapshotStateMachine',
                'detail': {
                    'metadata': {
                        'includes_slack_notification': True
                    },
                    'data': {
                        'slack': {
                            'text': JsonPath.format(
                                ':white_check_mark: *SnapshotShareSucceeded* | Snapshot ID: {}',
                                JsonPath.string_at('$.shared_snapshot_id')
                            )
                        }
                    }
                }
            },
        )

        make_snapshot_share_failure_message = Pass(
            self,
            'MakeSnapshotShareFailureMessage',
            parameters={
                'detailType': 'SnapShotShareFailed',
                'source': 'cdk-igvf-prod.snapshot-share.SnapshotStateMachine',
                'detail': {
                    'metadata': {
                        'includes_slack_notification': True
                    },
                    'data': {
                        'slack': {
                            'text': JsonPath.format(
                                ':x: *SnapshotShareFailed* | Database ID: {}',
                                self.db_identifier
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

        copy_latest_snapshot_lambda = PythonFunction(
            self,
            'MakeLatestSnapshotCopyLambda',
            entry='snapshot_share/lambdas/copy_snapshot',
            runtime=Runtime.PYTHON_3_9,
            index='main.py',
            handler='copy_latest_rds_snapshot',
            timeout=Duration.seconds(60),
            environment={'DATABASE_IDENTIFIER': self.db_identifier},
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

        copy_failed_procedure = make_snapshot_copy_failure_message.next(
            send_slack_notification
        )

        make_copy_of_latest_snapshot.add_catch(copy_failed_procedure)

        share_snapshot_lambda = PythonFunction(
            self,
            'ShareSnapshotCopyLambda',
            entry='snapshot_share/lambdas/share_snapshot',
            runtime=Runtime.PYTHON_3_9,
            index='main.py',
            handler='share_snapshot',
            timeout=Duration.seconds(60),
            environment={'SHARE_TO_ACCOUNTS': self.share_to_accounts},
        )

        share_snapshot_lambda.add_to_role_policy(
            PolicyStatement(
                actions=[
                    'rds:ModifyDBSnapshotAttribute'
                ],
                resources=['*'],
            )
        )

        share_failed_procedure = make_snapshot_share_failure_message.next(
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
            interval=Duration.seconds(60),
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
            make_snapshot_share_success_message
        ).next(
            send_slack_notification
        )

        state_machine = StateMachine(
            self,
            'StateMachine',
            definition=definition
        )

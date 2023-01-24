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
from aws_cdk.aws_stepfunctions import Wait
from aws_cdk.aws_stepfunctions import WaitTime
from aws_cdk.aws_stepfunctions import Fail

from aws_cdk.aws_stepfunctions_tasks import LambdaInvoke

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

        succeed = Succeed(self, 'Succeed')

        copy_latest_snapshot_lambda = PythonFunction(
            self,
            'MakeLatestSnapshotCopyLambda',
            entry='lambdas/copy_snapshot',
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
            entry='lambdas/share_snapshot',
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

        share_snapshot.add_catch(share_failed)



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
            succeed
        )


        state_machine = StateMachine(
            self,
            'StateMachine',
            definition=definition
        )

app = App()

copy_snapshot_stepfunction = CopySnapshotStepFunction(app, 'CopySnapshotStepFunction', env=IGVF_DEV_ENV)

app.synth()

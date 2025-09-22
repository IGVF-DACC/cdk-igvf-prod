from aws_cdk import Stack
from aws_cdk import Size
from aws_cdk import Duration

from aws_cdk.aws_ec2 import SubnetSelection
from aws_cdk.aws_ec2 import SubnetType

from aws_cdk.aws_ecs import AwsLogDriverMode
from aws_cdk.aws_ecs import LogDriver
from aws_cdk.aws_ecs import ContainerImage

from aws_cdk.aws_secretsmanager import Secret as SMSecret

from aws_cdk.aws_ecr_assets import Platform

from aws_cdk.aws_iam import Role
from aws_cdk.aws_iam import ServicePrincipal

from aws_cdk.aws_batch import FargateComputeEnvironment
from aws_cdk.aws_batch import JobQueue
from aws_cdk.aws_batch import EcsFargateContainerDefinition
from aws_cdk.aws_batch import EcsJobDefinition
from aws_cdk.aws_batch import Secret

from aws_cdk.aws_events import Rule
from aws_cdk.aws_events import Schedule
from aws_cdk.aws_events import EventPattern
from aws_cdk.aws_events import EventField
from aws_cdk.aws_events import Connection
from aws_cdk.aws_events import ApiDestination
from aws_cdk.aws_events import RuleTargetInput

from aws_cdk.aws_events_targets import BatchJob
from aws_cdk.aws_events_targets import ApiDestination as TargetApiDestination

from aws_cdk.aws_ssm import StringParameter

from aws_cdk.aws_logs import RetentionDays

from aws_cdk.aws_ec2 import Vpc

from constructs import Construct


class IGVFFileTransferStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = Vpc.from_lookup(
            self,
            'Vpc',
            vpc_id='vpc-0d874b77b42510f1b'
        )

        compute_environment = FargateComputeEnvironment(
            self,
            'ComputeEnvironment',
            vpc=vpc,
            vpc_subnets=SubnetSelection(
                subnet_type=SubnetType.PUBLIC,
            ),
            compute_environment_name='IGVFFileTransferCompute',
            maxv_cpus=2
        )

        file_transfer_job_queue = JobQueue(
            self,
            'FileTransferJobQueue',
            job_queue_name='IGVFFileTransferJobQueue',
        )

        file_transfer_job_queue.add_compute_environment(
            compute_environment,
            1
        )

        metadata_dump_job_queue = JobQueue(
            self,
            'MetadatadumpJobQueue',
            job_queue_name='IGVFMetadataDumpJobQueue',
        )

        metadata_dump_job_queue.add_compute_environment(
            compute_environment,
            1
        )

        job_role = Role(
            self,
            'IGVFFileTransferJobRole',
            assumed_by=ServicePrincipal(
                'ecs-tasks.amazonaws.com'
            )
        )

        igvf_file_transfer_user_portal_keys = SMSecret.from_secret_complete_arn(
            self,
            'IGVFFileTransferUserPortalKeys',
            'arn:aws:secretsmanager:us-west-2:035226225042:secret:igvf-files-transfer-user-portal-keys-J0yWyn'
        )

        igvf_file_transfer_user_access_key_secret = SMSecret.from_secret_complete_arn(
            self,
            'IGVFFileTransferUserAccessKeySecret',
            'arn:aws:secretsmanager:us-west-2:035226225042:secret:igvf-files-transfer-user-access-key-secret-1H0EXY'
        )

        igvf_file_transfer_container = EcsFargateContainerDefinition(
            self,
            'IGVFFileTransferContainer',
            assign_public_ip=True,
            image=ContainerImage.from_asset(
                './docker',
                platform=Platform.LINUX_AMD64,
            ),
            memory=Size.mebibytes(2048),
            cpu=1,
            environment={},
            secrets={
                'ACCESS_KEY': Secret.from_secrets_manager(
                    secret=igvf_file_transfer_user_access_key_secret,
                    field='ACCESS_KEY',
                ),
                'SECRET_ACCESS_KEY': Secret.from_secrets_manager(
                    secret=igvf_file_transfer_user_access_key_secret,
                    field='SECRET_ACCESS_KEY',
                ),
                'PORTAL_KEY': Secret.from_secrets_manager(
                    secret=igvf_file_transfer_user_portal_keys,
                    field='portal_key',
                ),
                'PORTAL_SECRET_KEY': Secret.from_secrets_manager(
                    secret=igvf_file_transfer_user_portal_keys,
                    field='portal_secret_key',
                )
            },
            logging=LogDriver.aws_logs(
                stream_prefix='igvf-file-transfer',
                mode=AwsLogDriverMode.NON_BLOCKING,
                log_retention=RetentionDays.ONE_MONTH,
            )
        )

        igvf_metadata_dump_container = EcsFargateContainerDefinition(
            self,
            'IGVFMetadataDumpContainer',
            assign_public_ip=True,
            image=ContainerImage.from_asset(
                './docker',
                platform=Platform.LINUX_AMD64,
            ),
            memory=Size.mebibytes(10000),
            cpu=1,
            environment={},
            secrets={
                'ACCESS_KEY': Secret.from_secrets_manager(
                    secret=igvf_file_transfer_user_access_key_secret,
                    field='ACCESS_KEY',
                ),
                'SECRET_ACCESS_KEY': Secret.from_secrets_manager(
                    secret=igvf_file_transfer_user_access_key_secret,
                    field='SECRET_ACCESS_KEY',
                ),
                'PORTAL_KEY': Secret.from_secrets_manager(
                    secret=igvf_file_transfer_user_portal_keys,
                    field='portal_key',
                ),
                'PORTAL_SECRET_KEY': Secret.from_secrets_manager(
                    secret=igvf_file_transfer_user_portal_keys,
                    field='portal_secret_key',
                )
            },
            command=['./run-dump.sh'],
            logging=LogDriver.aws_logs(
                stream_prefix='igvf-file-transfer',
                mode=AwsLogDriverMode.NON_BLOCKING,
                log_retention=RetentionDays.ONE_MONTH,
            )
        )

        file_transfer_job_definition = EcsJobDefinition(
            self,
            'IGVFFileTransferJobDef',
            container=igvf_file_transfer_container,
            timeout=Duration.hours(18),
        )

        metadata_dump_job_definition = EcsJobDefinition(
            self,
            'MetadataDumpJobDef',
            container=igvf_metadata_dump_container,
            timeout=Duration.hours(1),
        )

        start_igvf_file_transfer_rule = Rule(
            self,
            'start-igvf-file-transfer',
            schedule=Schedule.cron(
                minute='59',
                hour='6',
                day='*',
                month='*',
                year='*'
            ),
        )

        start_igvf_metadata_dump_rule = Rule(
            self,
            'start-igvf-metadata-dump',
            schedule=Schedule.cron(
                minute='59',
                hour='9',
                day='*',
                month='*',
                year='*'
            ),
        )

        igvf_file_transfer_target = BatchJob(
            job_queue_arn=file_transfer_job_queue.job_queue_arn,
            job_queue_scope=file_transfer_job_queue,
            job_definition_arn=file_transfer_job_definition.job_definition_arn,
            job_definition_scope=file_transfer_job_definition,
            job_name='IGVFFileTransferBatchJob',
            retry_attempts=0,
        )

        igvf_metadata_dump_target = BatchJob(
            job_queue_arn=metadata_dump_job_queue.job_queue_arn,
            job_queue_scope=metadata_dump_job_queue,
            job_definition_arn=metadata_dump_job_definition.job_definition_arn,
            job_definition_scope=metadata_dump_job_definition,
            job_name='IGVFMetadataDumpBatchJob',
            retry_attempts=0,
        )

        start_igvf_file_transfer_rule.add_target(
            igvf_file_transfer_target
        )

        start_igvf_metadata_dump_rule.add_target(
            igvf_metadata_dump_target
        )

        connection = Connection.from_event_bus_arn(
            self,
            'Connection',
            connection_arn='arn:aws:events:us-west-2:035226225042:connection/AwsIgvfProdSlackWebhookConnectionA3A57238-fgUoGdv828dW/46172d44-83a8-4c1e-9790-15f208e3477b',
            connection_secret_arn='arn:aws:secretsmanager:us-west-2:035226225042:secret:events!connection/AwsIgvfProdSlackWebhookConnectionA3A57238-fgUoGdv828dW/71939509-efa5-454c-9552-8a64ec9ebf84-bUCYqB',
        )

        endpoint = StringParameter.from_string_parameter_name(
            self,
            'SlackWebhookUrl',
            string_parameter_name='SLACK_WEBHOOK_URL_FOR_AWS_IGVF_PROD_CHANNEL',
        )

        api_destination = ApiDestination(
            self,
            'IGVFFileTransferSlackNotification',
            connection=connection,
            endpoint=endpoint.string_value,
        )

        transfer_succeeded_transformed_event = RuleTargetInput.from_object(
            {
                'text': f':white_check_mark: *IGVFFileTransferSucceeded* | {file_transfer_job_queue.job_queue_arn}'
            }
        )

        transfer_failed_transformed_event = RuleTargetInput.from_object(
            {
                'text': f':x: *IGVFFileTransferFailed* | {file_transfer_job_queue.job_queue_arn}'
            }
        )

        transfer_succeeded_outcome_notification_rule = Rule(
            self,
            'NotifySlackIGVFFileTransferSucceeded',
            event_pattern=EventPattern(
                source=['aws.batch'],
                detail_type=['Batch Job State Change'],
                detail={
                    'status': ['SUCCEEDED'],
                    'jobQueue': [f'{file_transfer_job_queue.job_queue_arn}'],
                }
            ),
            targets=[
                TargetApiDestination(
                    api_destination=api_destination,
                    event=transfer_succeeded_transformed_event,
                )
            ]
        )

        transfer_failed_outcome_notification_rule = Rule(
            self,
            'NotifySlackIGVFFileTransferFailed',
            event_pattern=EventPattern(
                source=['aws.batch'],
                detail_type=['Batch Job State Change'],
                detail={
                    'status': ['FAILED'],
                    'jobQueue': [f'{file_transfer_job_queue.job_queue_arn}'],
                }
            ),
            targets=[
                TargetApiDestination(
                    api_destination=api_destination,
                    event=transfer_failed_transformed_event,
                )
            ]
        )

        dump_succeeded_transformed_event = RuleTargetInput.from_object(
            {
                'text': f':white_check_mark: *IGVFMetadataDumpSucceeded* | {metadata_dump_job_queue.job_queue_arn}'
            }
        )

        dump_failed_transformed_event = RuleTargetInput.from_object(
            {
                'text': f':x: *IGVFMetadataDumpFailed* | {metadata_dump_job_queue.job_queue_arn}'
            }
        )

        dump_succeeded_outcome_notification_rule = Rule(
            self,
            'NotifySlackIGVFMetadataDumpSucceeded',
            event_pattern=EventPattern(
                source=['aws.batch'],
                detail_type=['Batch Job State Change'],
                detail={
                    'status': ['SUCCEEDED'],
                    'jobQueue': [f'{metadata_dump_job_queue.job_queue_arn}'],
                }
            ),
            targets=[
                TargetApiDestination(
                    api_destination=api_destination,
                    event=dump_succeeded_transformed_event,
                )
            ]
        )

        dump_failed_outcome_notification_rule = Rule(
            self,
            'NotifySlackIGVFMetadataDumpFailed',
            event_pattern=EventPattern(
                source=['aws.batch'],
                detail_type=['Batch Job State Change'],
                detail={
                    'status': ['FAILED'],
                    'jobQueue': [f'{metadata_dump_job_queue.job_queue_arn}'],
                }
            ),
            targets=[
                TargetApiDestination(
                    api_destination=api_destination,
                    event=dump_failed_transformed_event,
                )
            ]
        )

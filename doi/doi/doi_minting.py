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


class DoiMintingStack(Stack):

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
            compute_environment_name='DoiMintingCompute',
            maxv_cpus=2
        )

        doi_minting_job_queue = JobQueue(
            self,
            'DoiMintingJobQueue',
            job_queue_name='DoiMintingJobQueue',
        )

        doi_minting_job_queue.add_compute_environment(
            compute_environment,
            1
        )

        job_role = Role(
            self,
            'DoiMintingJobRole',
            assumed_by=ServicePrincipal(
                'ecs-tasks.amazonaws.com'
            )
        )

        igvf_doi_minting_user_portal_keys = SMSecret.from_secret_complete_arn(
            self,
            'IgvfDoiMintingUserPortalKeys',
            'arn:aws:secretsmanager:us-west-2:035226225042:secret:igvf-doi-minting-user-portal-keys-vXwOg4'
        )

        doi_minting_crossref_credentials = SMSecret.from_secret_complete_arn(
            self,
            'DoiMintingCrossrefCredentials',
            'arn:aws:secretsmanager:us-west-2:035226225042:secret:doi-minting-crossref-credentials-r4Yvfx'
        )

        doi_minting_container = EcsFargateContainerDefinition(
            self,
            'DoiMintingContainer',
            assign_public_ip=True,
            image=ContainerImage.from_asset(
                './docker',
                platform=Platform.LINUX_AMD64,
            ),
            memory=Size.mebibytes(2048),
            cpu=1,
            environment={'CROSSREF_SERVER': 'https://doi.crossref.org/servlet/deposit',
                         'IGVF_SERVER': 'https://api.data.igvf.org'},
            secrets={
                'PORTAL_KEY': Secret.from_secrets_manager(
                    secret=igvf_doi_minting_user_portal_keys,
                    field='portal_key',
                ),
                'PORTAL_SECRET_KEY': Secret.from_secrets_manager(
                    secret=igvf_doi_minting_user_portal_keys,
                    field='portal_secret_key',
                ),
                'CROSSREF_LOGIN': Secret.from_secrets_manager(
                    secret=doi_minting_crossref_credentials,
                    field='crossref_login',
                ),
                'CROSSREF_PASSWORD': Secret.from_secrets_manager(
                    secret=doi_minting_crossref_credentials,
                    field='crossref_password',
                ),
            },
            logging=LogDriver.aws_logs(
                stream_prefix='doi-minting',
                mode=AwsLogDriverMode.NON_BLOCKING,
                log_retention=RetentionDays.ONE_MONTH,
            )
        )

        doi_minting_job_definition = EcsJobDefinition(
            self,
            'DoiMintingJobDefinition',
            container=doi_minting_container,
            timeout=Duration.hours(8),
        )

        start_doi_minting_rule = Rule(
            self,
            'StartDoiMintingRule',
            schedule=Schedule.cron(
                minute='55',
                hour='5',
                day='*',
                month='*',
                year='*'
            ),
        )

        doi_minting_target = BatchJob(
            job_queue_arn=doi_minting_job_queue.job_queue_arn,
            job_queue_scope=doi_minting_job_queue,
            job_definition_arn=doi_minting_job_definition.job_definition_arn,
            job_definition_scope=doi_minting_job_definition,
            job_name='DoiMintingBatchJob',
            retry_attempts=0,
        )

        start_doi_minting_rule.add_target(
            doi_minting_target
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
            'DoiMintingSlackNotification',
            connection=connection,
            endpoint=endpoint.string_value,
        )

        doi_minting_succeeded_transformed_event = RuleTargetInput.from_object(
            {
                'text': f':white_check_mark: *DoiMintingSucceeded* | {doi_minting_job_queue.job_queue_arn}'
            }
        )

        doi_minting_failed_transformed_event = RuleTargetInput.from_object(
            {
                'text': f':x: *DoiMintingFailed* | {doi_minting_job_queue.job_queue_arn}'
            }
        )

        doi_minting_succeeded_outcome_notification_rule = Rule(
            self,
            'NotifySlackDoiMintingSucceeded',
            event_pattern=EventPattern(
                source=['aws.batch'],
                detail_type=['Batch Job State Change'],
                detail={
                    'status': ['SUCCEEDED'],
                    'jobQueue': [f'{doi_minting_job_queue.job_queue_arn}'],
                }
            ),
            targets=[
                TargetApiDestination(
                    api_destination=api_destination,
                    event=doi_minting_succeeded_transformed_event,
                )
            ]
        )

        doi_minting_failed_outcome_notification_rule = Rule(
            self,
            'NotifySlackDoiMintingFailed',
            event_pattern=EventPattern(
                source=['aws.batch'],
                detail_type=['Batch Job State Change'],
                detail={
                    'status': ['FAILED'],
                    'jobQueue': [f'{doi_minting_job_queue.job_queue_arn}'],
                }
            ),
            targets=[
                TargetApiDestination(
                    api_destination=api_destination,
                    event=doi_minting_failed_transformed_event,
                )
            ]
        )

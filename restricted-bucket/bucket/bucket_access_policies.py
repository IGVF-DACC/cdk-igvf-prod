from aws_cdk import App
from aws_cdk import Stack
from aws_cdk import SecretValue

from aws_cdk.aws_iam import AccessKey
from aws_cdk.aws_iam import User
from aws_cdk.aws_iam import ManagedPolicy
from aws_cdk.aws_iam import PolicyStatement

from aws_cdk.aws_secretsmanager import Secret

from constructs import Construct

from bucket.bucket_storage import RestrictedBucketStorage

from typing import Any


class RestrictedBucketAccessPolicies(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            bucket_storage: RestrictedBucketStorage,
            **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.bucket_storage = bucket_storage

        self.download_igvf_restricted_files_policy_statement = PolicyStatement(
            sid='AllowReadFromRestrictedFilesBucket',
            resources=[
                self.bucket_storage.restricted_files_bucket.bucket_arn,
                self.bucket_storage.restricted_files_bucket.arn_for_objects(
                    '*'),
            ],
            actions=[
                's3:GetObjectVersion',
                's3:GetObject',
                's3:GetBucketAcl',
                's3:ListBucket',
                's3:GetBucketLocation'
            ]
        )

        self.upload_igvf_restricted_files_policy_statement = PolicyStatement(
            sid='AllowReadAndWriteToRestrictedFilesBucket',
            resources=[
                self.bucket_storage.restricted_files_bucket.bucket_arn,
                self.bucket_storage.restricted_files_bucket.arn_for_objects(
                    '*'),
            ],
            actions=[
                's3:PutObject',
                's3:GetObjectVersion',
                's3:GetObject',
                's3:GetBucketAcl',
                's3:ListBucket',
                's3:GetBucketLocation',
            ]
        )

        self.restricted_federated_token_policy_statement = PolicyStatement(
            sid='AllowGenerateFederatedTokenRestrictedFiles',
            resources=[
                '*',
            ],
            actions=[
                'iam:PassRole',
                'sts:GetFederationToken',
            ]
        )

        self.download_igvf_restricted_files_policy = ManagedPolicy(
            self,
            'DownloadIgvfRestrictedFilesPolicy',
            managed_policy_name='download-igvf-restricted-files',
            statements=[
                self.download_igvf_restricted_files_policy_statement,
            ],
        )

        self.upload_igvf_restricted_files_policy = ManagedPolicy(
            self,
            'UploadIgvfRestrictedFilesPolicy',
            managed_policy_name='upload-igvf-restricted-files',
            statements=[
                self.upload_igvf_restricted_files_policy_statement,
                self.restricted_federated_token_policy_statement,
            ],
        )

        self.upload_igvf_restricted_files_user = User(
            self,
            'UploadIgvfRestrictedFilesUser',
            user_name='upload-igvf-restricted-files',
            managed_policies=[
                self.upload_igvf_restricted_files_policy,
            ]
        )

        self.upload_igvf_restricted_files_user_access_key = AccessKey(
            self,
            'UploadIgvfRestrictedFilesUserAccessKey',
            user=self.upload_igvf_restricted_files_user,
        )

        self.upload_igvf_restricted_files_user_access_key_secret = Secret(
            self,
            'UploadIgvfRestrictedFilesUserAccessKeySecret',
            secret_name='upload-igvf-restricted-files-user-access-key-secret',
            secret_object_value={
                'ACCESS_KEY': SecretValue.unsafe_plain_text(
                    self.upload_igvf_restricted_files_user_access_key.access_key_id,
                ),
                'SECRET_ACCESS_KEY': self.upload_igvf_restricted_files_user_access_key.secret_access_key,
            },
        )

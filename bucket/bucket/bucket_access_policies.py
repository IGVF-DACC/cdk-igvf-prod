from aws_cdk import App
from aws_cdk import Stack
from aws_cdk import SecretValue

from aws_cdk.aws_iam import AccessKey
from aws_cdk.aws_iam import User
from aws_cdk.aws_iam import ManagedPolicy
from aws_cdk.aws_iam import PolicyStatement

from aws_cdk.aws_secretsmanager import Secret

from constructs import Construct

from bucket.bucket_storage import BucketStorage

from typing import Any


class BucketAccessPolicies(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            bucket_storage: BucketStorage,
            **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.bucket_storage = bucket_storage

        self.download_igvf_files_policy_statement = PolicyStatement(
            sid='AllowReadFromFilesAndBlobsBuckets',
            resources=[
                self.bucket_storage.files_bucket.bucket_arn,
                self.bucket_storage.files_bucket.arn_for_objects('*'),
                self.bucket_storage.blobs_bucket.bucket_arn,
                self.bucket_storage.blobs_bucket.arn_for_objects('*'),
            ],
            actions=[
                's3:GetObjectVersion',
                's3:GetObject',
                's3:GetBucketAcl',
                's3:ListBucket',
                's3:GetBucketLocation'
            ]
        )

        self.upload_igvf_files_policy_statement = PolicyStatement(
            sid='AllowReadAndWriteToFilesAndBlobsBuckets',
            resources=[
                self.bucket_storage.files_bucket.bucket_arn,
                self.bucket_storage.files_bucket.arn_for_objects('*'),
                self.bucket_storage.blobs_bucket.bucket_arn,
                self.bucket_storage.blobs_bucket.arn_for_objects('*'),
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

        self.federated_token_policy_statement = PolicyStatement(
            sid='AllowGenerateFederatedToken',
            resources=[
                '*',
            ],
            actions=[
                'iam:PassRole',
                'sts:GetFederationToken',
            ]
        )

        self.download_igvf_files_policy = ManagedPolicy(
            self,
            'DownloadIgvfFilesPolicy',
            managed_policy_name='download-igvf-files',
            statements=[
                self.download_igvf_files_policy_statement,
            ],
        )

        self.upload_igvf_files_policy = ManagedPolicy(
            self,
            'UploadIgvfFilesPolicy',
            managed_policy_name='upload-igvf-files',
            statements=[
                self.upload_igvf_files_policy_statement,
                self.federated_token_policy_statement,
            ],
        )

        self.upload_igvf_files_user = User(
            self,
            'UploadIgvfFilesUser',
            user_name='upload-igvf-files',
            managed_policies=[
                self.upload_igvf_files_policy,
            ]
        )

        self.upload_igvf_files_user_access_key = AccessKey(
            self,
            'UploadIgvfFilesUserAccessKey',
            user=self.upload_igvf_files_user,
        )

        self.upload_igvf_files_user_access_key_secret = Secret(
            self,
            'UploadIgvfFilesUserAccessKeySecret',
            secret_name='upload-igvf-files-user-access-key-secret',
            secret_object_value={
                'ACCESS_KEY': SecretValue.unsafe_plain_text(
                    self.upload_igvf_files_user_access_key.access_key_id,
                ),
                'SECRET_ACCESS_KEY': self.upload_igvf_files_user_access_key.secret_access_key,
            },
        )

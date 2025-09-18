from aws_cdk import App
from aws_cdk import Stack
from aws_cdk import RemovalPolicy

from aws_cdk.aws_iam import AccountPrincipal
from aws_cdk.aws_iam import ArnPrincipal
from aws_cdk.aws_iam import ManagedPolicy
from aws_cdk.aws_iam import PolicyStatement

from aws_cdk.aws_s3 import Bucket
from aws_cdk.aws_s3 import CorsRule
from aws_cdk.aws_s3 import HttpMethods

from constructs import Construct

from typing import Any
from typing import List


BLOBS_BUCKET_NAME = 'igvf-blobs'
FILES_BUCKET_NAME = 'igvf-files'

IGVF_TRANSFER_USER_ARN = 'arn:aws:iam::407227577691:user/igvf-files-transfer'

S3_BATCH_OPERATION_COPY_ROLE_ARN = 'arn:aws:iam::407227577691:role/IGVFBucketAccessPolicies-S3BatchOperationCopyObject-6wmJYD0XgxSv'


BROWSER_UPLOAD_CORS = CorsRule(
    allowed_methods=[
        HttpMethods.GET,
        HttpMethods.HEAD,
        HttpMethods.POST,
        HttpMethods.PUT,
    ],
    allowed_origins=[
        'https://*-script.googleusercontent.com'
    ],
    allowed_headers=[
        '*',
    ],
    exposed_headers=[
        'Content-Length',
        'Content-Range',
        'Content-Type',
        'ETag',
    ],
    max_age=3000,
)


CORS = CorsRule(
    allowed_methods=[
        HttpMethods.GET,
        HttpMethods.HEAD,
    ],
    allowed_origins=[
        '*'
    ],
    allowed_headers=[
        'Accept',
        'Origin',
        'Range',
        'X-Requested-With',
        'Cache-Control',
    ],
    exposed_headers=[
        'Content-Length',
        'Content-Range',
        'Content-Type',
        'ETag',
    ],
    max_age=3000,
)


def generate_read_access_policy_for_bucket(
        *,
        sid: str,
        principals: List[AccountPrincipal],
        resources: List[str]
) -> PolicyStatement:
    return PolicyStatement(
        sid=sid,
        principals=principals,
        resources=resources,
        actions=[
            's3:GetObjectVersion',
            's3:GetObject',
            's3:GetBucketAcl',
            's3:ListBucket',
            's3:GetBucketLocation'
        ]
    )


class BucketStorage(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.blobs_logs_bucket = Bucket(
            self,
            'BlobsLogsBucket',
            bucket_name=f'{BLOBS_BUCKET_NAME}-logs',
            removal_policy=RemovalPolicy.RETAIN,
        )

        self.blobs_bucket = Bucket(
            self,
            'BlobsBucket',
            bucket_name=f'{BLOBS_BUCKET_NAME}',
            cors=[
                CORS
            ],
            removal_policy=RemovalPolicy.RETAIN,
            server_access_logs_bucket=self.blobs_logs_bucket,
            versioned=True,
        )

        self.blobs_bucket_read_access_policy = generate_read_access_policy_for_bucket(
            sid='AllowReadFromIgvfDevAndStagingAccounts',
            principals=[
                AccountPrincipal('109189702753'),  # igvf-dev
                AccountPrincipal('920073238245'),  # igvf-staging
            ],
            resources=[
                self.blobs_bucket.bucket_arn,
                self.blobs_bucket.arn_for_objects('*'),
            ]
        )

        self.blobs_bucket.add_to_resource_policy(
            self.blobs_bucket_read_access_policy
        )

        self.files_logs_bucket = Bucket(
            self,
            'FilesLogsBucket',
            bucket_name=f'{FILES_BUCKET_NAME}-logs',
            removal_policy=RemovalPolicy.RETAIN,
        )

        self.files_bucket = Bucket(
            self,
            'FilesBucket',
            bucket_name=f'{FILES_BUCKET_NAME}',
            cors=[
                BROWSER_UPLOAD_CORS,
                CORS
            ],
            removal_policy=RemovalPolicy.RETAIN,
            server_access_logs_bucket=self.files_logs_bucket,
            versioned=True,
        )

        self.files_bucket_read_access_policy = generate_read_access_policy_for_bucket(
            sid='AllowReadFromIgvfDevAndStagingAccounts',
            principals=[
                AccountPrincipal('109189702753'),  # igvf-dev
                AccountPrincipal('920073238245'),  # igvf-staging
            ],
            resources=[
                self.files_bucket.bucket_arn,
                self.files_bucket.arn_for_objects('*'),
            ]
        )

        self.files_bucket.add_to_resource_policy(
            self.files_bucket_read_access_policy
        )

        self.igvf_transfer_user_principal = ArnPrincipal(
            IGVF_TRANSFER_USER_ARN
        )

        self.igvf_transfer_user_upload_bucket_policy_statement = PolicyStatement(
            sid='AllowIgvfTransferUserReadFromUploadBucket',
            principals=[
                self.igvf_transfer_user_principal
            ],
            resources=[
                self.files_bucket.bucket_arn,
                self.files_bucket.arn_for_objects('*'),
            ],
            actions=[
                's3:GetBucketAcl',
                's3:GetBucketLocation',
                's3:GetObject',
                's3:GetObjectTagging',
                's3:GetObjectVersion',
                's3:ListBucket',
                's3:PutObjectTagging'
            ]
        )

        self.files_bucket.add_to_resource_policy(
            self.igvf_transfer_user_upload_bucket_policy_statement,
        )

        self.s3_batch_operation_copy_object_role_read_access_policy = PolicyStatement(
            sid='AllowS3BatchOperationRoleReadFromUploadBucket',
            principals=[
                ArnPrincipal(S3_BATCH_OPERATION_COPY_ROLE_ARN)
            ],
            resources=[
                self.files_bucket.bucket_arn,
                self.files_bucket.arn_for_objects('*'),
            ],
            actions=[
                's3:GetObject',
                's3:GetObjectVersion',
                's3:GetObjectAcl',
                's3:GetObjectTagging',
                's3:GetObjectVersionAcl',
                's3:GetObjectVersionTagging',
                's3:ListBucket',
            ],
        )

        self.files_bucket.add_to_resource_policy(
            self.s3_batch_operation_copy_object_role_read_access_policy
        )

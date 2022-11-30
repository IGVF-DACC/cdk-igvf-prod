from aws_cdk import Stack

from constructs import Construct

from aws_cdk.aws_ec2 import SubnetConfiguration
from aws_cdk.aws_ec2 import SubnetType
from aws_cdk.aws_ec2 import Vpc

from typing import Any


class NetworkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.production_vpc = Vpc(
            self,
            'ProductionVpc',
            cidr='10.7.0.0/16',
            nat_gateways=0,
            subnet_configuration=[
                SubnetConfiguration(
                    name='public',
                    cidr_mask=20,
                    subnet_type=SubnetType.PUBLIC,
                ),
                SubnetConfiguration(
                    name='isolated',
                    cidr_mask=20,
                    subnet_type=SubnetType.PRIVATE_ISOLATED,
                ),
            ]
        )

import aws_cdk as cdk

from constructs import Construct

from aws_cdk.aws_chatbot import SlackChannelConfiguration

from aws_cdk.aws_sns import Topic

from notification.constructs.slack import SlackWebhook

from typing import Any


class NotificationStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.aws_igvf_prod_channel: SlackChannelConfiguration = SlackChannelConfiguration(
            self,
            'AwsIgvfProdChannel',
            slack_channel_configuration_name='aws-igvf-prod',
            slack_workspace_id='T1KMV4JJZ',
            slack_channel_id='C04CWLXF9RB',
        )
        self.alarm_notification_topic = Topic(
            self,
            'AwsIgvfProdChannelAlarmNotificationTopic',
        )
        self.aws_igvf_prod_channel.add_notification_topic(
            self.alarm_notification_topic
        )
        self.aws_igvf_prod_channel_slack_webhook: SlackWebhook = SlackWebhook(
            self,
            'AwsIgvfProdSlackWebhook',
        )

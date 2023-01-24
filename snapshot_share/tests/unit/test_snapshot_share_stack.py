import aws_cdk as core
import aws_cdk.assertions as assertions

from snapshot_share.snapshot_share_stack import SnapshotShareStack

# example tests. To run these tests, uncomment this file along with the example
# resource in snapshot_share/snapshot_share_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SnapshotShareStack(app, "snapshot-share")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

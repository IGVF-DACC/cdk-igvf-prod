from aws_cdk import App
from aws_cdk import Environment

from transfer.igvf import IGVFFileTransferStack


app = App()


US_WEST_2 = Environment(
    account='035226225042',
    region='us-west-2',
)


IGVFFileTransferStack(
    app,
    'IGVFFileTransferStack',
    env=US_WEST_2,
)


app.synth()

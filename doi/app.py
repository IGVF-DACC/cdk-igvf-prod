from aws_cdk import App
from aws_cdk import Environment

from doi.doi_minting import DoiMintingStack


US_WEST_2 = Environment(
    account='035226225042',
    region='us-west-2',
)
app = App()
DoiMintingStack(
    app,
    'DoiMintingStack',
    env=US_WEST_2,
)
app.synth()

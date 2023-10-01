import aws_cdk as cdk
import boto3

from sfn_alarm import SfnAlarmStack


app = cdk.App()
environment = app.node.try_get_context("environment")
account = boto3.client("sts").get_caller_identity()["Account"]
SfnAlarmStack(
    app,
    "SfnAlarmStack",
    env=cdk.Environment(account=account, region=environment["AWS_REGION"]),
    environment=environment,
)
app.synth()

from aws_cdk import (
    Duration,
    Stack,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_lambda as _lambda,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    aws_stepfunctions as sfn,
)
from constructs import Construct


class SfnAlarmStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, environment: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        sfn_definition = (
            sfn.Choice(self, "Bool?")
            .when(
                sfn.Condition.boolean_equals(variable="$.status", value=True),
                sfn.Succeed(self, "We did it!"),
            )
            .otherwise(sfn.Fail(self, "Job Failed", cause="Total", error="Failure"))
        )
        self.state_machine = sfn.StateMachine(
            self, "succeed_or_fail", definition=sfn_definition
        )

        self.sns_topic = sns.Topic(self, "AlarmTopic")

        self.printer_lambda = _lambda.Function(
            self,
            "Printer",
            code=_lambda.InlineCode("def lambda_handler(event, context): print(event)"),
            handler="index.lambda_handler",
            runtime=_lambda.Runtime.PYTHON_3_9,
        )

        # connect the AWS resources
        self.alarm = cloudwatch.Alarm(
            self,
            "SfnAlarm",
            metric=self.state_machine.metric_failed(
                statistic="sum", period=Duration.minutes(1)
            ),
            alarm_description="Step Function failed at least 1 time in 1 minute",
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            threshold=0,
            evaluation_periods=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        alarm_action = cloudwatch_actions.SnsAction(topic=self.sns_topic)
        self.alarm.add_alarm_action(alarm_action)
        self.alarm.add_ok_action(alarm_action)

        self.sns_topic.add_subscription(
            sns_subscriptions.LambdaSubscription(self.printer_lambda)
        )

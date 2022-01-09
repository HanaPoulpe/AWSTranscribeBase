"""Architecture for deployment"""
from aws_cdk import core as cdk
import aws_cdk.aws_iam as aws_iam
import aws_cdk.aws_lambda as aws_lambda
import aws_cdk.aws_s3 as aws_s3
import aws_cdk.aws_s3_notifications as aws_s3_notifications
import aws_cdk.aws_sns as aws_sns

from .code_from_asset2 import include_requirements

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core


class CdkStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a bucket to drop files in
        self.media_bucket = aws_s3.Bucket(
            self,
            "MediaBucket",
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
        )
        transcribe_policy = aws_iam.ManagedPolicy.from_managed_policy_arn(
            self,
            "TranscribeFullAccess",
            "arn:aws:iam::aws:policy/AmazonTranscribeFullAccess",
        )
        lambda_basic_execution = aws_iam.ManagedPolicy.from_managed_policy_arn(
            self,
            "LambdaBasicExecutionRole",
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        )

        # Create AWS Lambda for file processing
        processing_role = aws_iam.Role(
            self,
            "MediaProcessorRole",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com")
        )
        processing_role.add_managed_policy(transcribe_policy)
        processing_role.add_managed_policy(lambda_basic_execution)

        self.processing_lambda = aws_lambda.Function(
            self,
            "MediaProcessor",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler="handler.lambda_handler",
            code=include_requirements("src/awslambda/media_processor", "media_processor"),
            environment={
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": "MediaProcessor"
            },
            role=processing_role
        )
        self.media_bucket.grant_read_write(processing_role)

        for suffix in [".mp3", ".mp4", ".wav", ".flac", ".ogg", ".amr", ".webm"]:
            self.media_bucket.add_event_notification(
                aws_s3.EventType.OBJECT_CREATED,
                aws_s3_notifications.LambdaDestination(self.processing_lambda),
                aws_s3.NotificationKeyFilter(suffix=suffix)
            )

        # Create job output notification system
        self.sns_job_complete = aws_sns.Topic(
            self,
            "JobCompleteNotifications",
            topic_name="JobCompleteNotifications",
        )
        self.email_sender_lambda = aws_lambda.Function(
            self,
            "EMailNotification",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler="handler.lambda_handler",
            code=include_requirements("src/awslambda/email_notification", "email_notification"),
            environment={
                "DESTINATION_SNS": self.sns_job_complete.topic_arn,
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": "NOTIFIER",
            },
        )
        self.sns_job_complete.grant_publish(self.email_sender_lambda)
        for suffix in [".vtt", ".srt"]:
            self.media_bucket.add_event_notification(
                aws_s3.EventType.OBJECT_CREATED,
                aws_s3_notifications.LambdaDestination(self.processing_lambda),
                aws_s3.NotificationKeyFilter(suffix=suffix)
            )

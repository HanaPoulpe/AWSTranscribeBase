"""Create a SNS notfication once a transcibe job is completed"""
import os

import aws_lambda_powertools as alp
import aws_lambda_powertools.utilities.data_classes as aws_dataclasses
import aws_lambda_powertools.utilities.typing as aws_tyiping
import boto3

logger = alp.Logger()

@logger.inject_lambda_context
def lambda_handler(event: dict[str, any], context: aws_tyiping.LambdaContext) -> dict[str, any]:
    event = aws_dataclasses.S3Event(event)
    logger.info(f"Got event: {event.raw_event!r}")

    destination = os.getenv("DESTINATION_SNS")
    if not destination:
        logger.error("No destination set...")
        return {}

    with open("email_template.md", "r") as fp:
        body = fp.read()

    body = body.format(file_uri=f"s3://{event.bucket_name}/{event.object_key}")

    sns_client = boto3.client("sns")
    sns_client.publish(
        TopicArn=destination,
        Message=body,
        Subject=f"Transcribe job completion for file: s3://{event.bucket_name}/{event.object_key}",
    )

    return {}

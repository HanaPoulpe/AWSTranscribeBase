"""Creates a Transcribe Job from S3 event"""
import aws_lambda_powertools as alp
import aws_lambda_powertools.utilities.data_classes as aws_dataclasses
import aws_lambda_powertools.utilities.typing as aws_tyiping
import boto3

logger = alp.Logger()


@logger.inject_lambda_context
def lambda_handler(event: dict[str, any], context: aws_tyiping.LambdaContext):
    event = aws_dataclasses.S3Event(event)
    logger.info(f"Got event: {event.raw_event!r}")

    media_format = event.object_key.split(".")[-1]
    output_format = "srt"
    output_key = event.object_key[:-(1 + len(media_format))].replace(" ", "_")

    transcribe_client = boto3.client("transcribe")

    transcribe_job = transcribe_client.start_transcription_job(
        TranscriptionJobName=event.object_key.split("/")[-1],
        LanguageCode="en-AU",
        MediaFormat=media_format,
        Media={
            "MediaFileUri": f"s3://{event.bucket_name}/{event.object_key}",
        },
        OutputBucketName=event.bucket_name,
        OutputKey=output_key,
        Settings={
            "ShowSpeakerLabels": True,
            "MaxSpeakerLabels": 5,
            "ShowAlternatives": True,
            "MaxAlternatives": 3,
        },
        Subtitles={
            "Formats": [output_format],
        },
    )

    logger.info(f"Job details: {transcribe_job!r}")

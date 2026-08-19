import boto3
from botocore.exceptions import ClientError
import logging
import os

aws_access_key=os.getenv("AWS_ACCESS_KEY")
aws_secret_access=os.getenv("AWS_SECRET_ACCESS")
region_name=os.getenv("REGION_NAME")
aws_bucket=os.getenv("AWS_BUCKET")


aws = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access,
    region_name=region_name
)

s3 = aws.client("s3")


def uploads3(
        file_stream,
        file_name,
        bucket: str = aws_bucket
        ):

    try:
        s3.upload_fileobj(file_stream, bucket, file_name)
    except ClientError as e:
        logging.error(e)
        print("this is error")
        return False

    return True

# connection to aws needed for:
# upload files to s3
# from s3 file goes through rag then through pgvector rds

# for vector search only pgvector rds

# rds always needed if postgresql is uploaded to rds

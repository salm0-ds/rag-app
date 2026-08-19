import boto3
from botocore.exceptions import ClientError
import logging
import os



aws = boto3.Session(
    aws_access_key_id="AKIATDY3UKUU2VG5GQF6",
    aws_secret_access_key="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",
    region_name="eu-west-2"
)

s3 = aws.client("s3")


def upload_to_s3(
        file_name: str, 
        bucket: str = "ragapp-userfile-s3bucket-214269449513-eu-west-2-an"
        ):
    
    try:
        send_file = s3.upload_file(f"uploaded_docs/{file_name}", bucket, file_name)
    except ClientError as e:
        logging.error(e)
        return False
    except FileNotFoundError as e:
        logging.error(e)
        return False
    return 


def uploads3(
        file_stream,
        file_name,
        bucket: str = "ragapp-userfile-s3bucket-214269449513-eu-west-2-an"
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

def download_from_s3(
        file_name: str,
        bucket: str = "ragapp-userfile-s3bucket-214269449513-eu-west-2-an"
):
    try:
        s3.download_file(
            bucket,
            file_name,
            f"uploaded_docs/{file_name}"
        )
    except ClientError as e:
        logging.error(e)
    

    return {
        "message": "download succesful"
    }


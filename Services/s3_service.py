import boto3
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME

def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

def upload_to_s3(file_obj, filename: str) -> str:
    s3_client = get_s3_client()
    s3_key = f"resumes/{filename}"
    s3_client.upload_fileobj(file_obj, S3_BUCKET_NAME, s3_key)
    return s3_key
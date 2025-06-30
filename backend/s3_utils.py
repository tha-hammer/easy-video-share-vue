import boto3
import uuid
from datetime import datetime, timedelta
from typing import Optional
from botocore.exceptions import ClientError
from config import settings


def get_s3_client():
    """Get configured S3 client using environment variables or IAM role."""
    return boto3.client(
        's3',
        region_name="us-east-1",  # Use the region from settings
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def generate_presigned_url(bucket_name: str, object_key: str, client_method: str,content_type: str, expiration: int = 3600) -> str:
    """
    Generate a presigned URL for S3 upload
    
    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key (path)
        content_type: MIME type of the file
        expiration: URL expiration time in seconds (default: 1 hour)
    
    Returns:
        Presigned URL string for direct upload to S3
    """
    s3_client = get_s3_client()
     
    try:
        params = {
            'Bucket': bucket_name,
            'Key': object_key
        }

        # Conditionally add ContentType for 'put_object' operations only
        if client_method == 'put_object' and content_type is not None:
            params['ContentType'] = content_type
        # No 'else' needed, ContentType is not added for 'get_object'

        presigned_url = s3_client.generate_presigned_url(
            ClientMethod=client_method, # Use the new parameter here
            Params=params,
            ExpiresIn=expiration
        )
        return presigned_url
    except ClientError as e:
        raise Exception(f"Failed to generate presigned URL: {str(e)}")


def generate_s3_key(filename: str, job_id: str) -> str:
    """
    Generate a unique S3 object key for uploaded video
    
    Args:
        filename: Original filename
        job_id: Unique job identifier
    
    Returns:
        S3 object key in format: uploads/{job_id}/{timestamp}_{filename}
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    # Clean filename to be S3-safe
    clean_filename = filename.replace(' ', '_').replace('(', '').replace(')', '')
    return f"uploads/{job_id}/{timestamp}_{clean_filename}"


def download_file_from_s3(bucket: str, key: str, local_path: str) -> None:
    """
    Download a file from S3 to local filesystem
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        local_path: Local file path to save the downloaded file
    """
    s3_client = get_s3_client()
    
    try:
        s3_client.download_file(bucket, key, local_path)
    except ClientError as e:
        raise Exception(f"Failed to download file from S3: {str(e)}")


def upload_file_to_s3(local_path: str, bucket: str, key: str) -> str:
    """
    Upload a local file to S3
    
    Args:
        local_path: Local file path to upload
        bucket: S3 bucket name
        key: S3 object key (destination path)
    
    Returns:
        S3 URL of the uploaded file
    """
    s3_client = get_s3_client()
    
    try:
        s3_client.upload_file(local_path, bucket, key)
        return f"https://{bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
    except ClientError as e:
        raise Exception(f"Failed to upload file to S3: {str(e)}")


def get_s3_file_size(bucket: str, key: str) -> int:
    """
    Get the size of an S3 object
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
    
    Returns:
        File size in bytes
    """
    s3_client = get_s3_client()
    
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        return response['ContentLength']
    except ClientError as e:
        raise Exception(f"Failed to get S3 object size: {str(e)}")

import boto3
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from botocore.exceptions import ClientError
from config import settings


def get_s3_client():
    """Get configured S3 client using environment variables or IAM role."""
    return boto3.client(
        's3',
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

print(f"DEBUG: AWS_REGION = {settings.AWS_REGION}")

def generate_presigned_url(bucket_name: str, object_key: str, client_method: str, content_type: str, expiration: int = 3600) -> str:
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


def calculate_optimal_chunk_size(file_size: int, is_mobile: bool = False) -> tuple[int, int]:
    """
    Calculate optimal chunk size and max concurrent uploads based on file size and device type
    
    Args:
        file_size: Size of file in bytes
        is_mobile: Whether this is a mobile device
    
    Returns:
        Tuple of (chunk_size, max_concurrent_uploads)
    """
    MB = 1024 * 1024
    GB = 1024 * MB
    
    if is_mobile:
        # Mobile devices: smaller chunks, fewer concurrent uploads
        if file_size <= 100 * MB:
            return 5 * MB, 2  # 5MB chunks, 2 concurrent
        elif file_size <= 500 * MB:
            return 8 * MB, 3  # 8MB chunks, 3 concurrent
        elif file_size <= 1 * GB:
            return 10 * MB, 3  # 10MB chunks, 3 concurrent
        else:
            return 15 * MB, 4  # 15MB chunks, 4 concurrent
    else:
        # Desktop: larger chunks, more concurrent uploads
        if file_size <= 100 * MB:
            return 10 * MB, 4  # 10MB chunks, 4 concurrent
        elif file_size <= 500 * MB:
            return 15 * MB, 6  # 15MB chunks, 6 concurrent
        elif file_size <= 1 * GB:
            return 20 * MB, 6  # 20MB chunks, 6 concurrent
        else:
            return 25 * MB, 8  # 25MB chunks, 8 concurrent


def initiate_multipart_upload(bucket_name: str, object_key: str, content_type: str) -> str:
    """
    Initiate a multi-part upload to S3
    
    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key
        content_type: MIME type of the file
    
    Returns:
        Upload ID for the multi-part upload
    """
    s3_client = get_s3_client()
    
    try:
        response = s3_client.create_multipart_upload(
            Bucket=bucket_name,
            Key=object_key,
            ContentType=content_type,
            Metadata={
                'uploaded_at': datetime.utcnow().isoformat(),
                'upload_type': 'multipart'
            }
        )
        return response['UploadId']
    except ClientError as e:
        raise Exception(f"Failed to initiate multipart upload: {str(e)}")


def generate_presigned_url_for_part(
    bucket_name: str, 
    object_key: str, 
    upload_id: str, 
    part_number: int, 
    expiration: int = 3600
) -> str:
    """
    Generate a presigned URL for uploading a specific part
    
    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key
        upload_id: Multi-part upload ID
        part_number: Part number (1-based)
        expiration: URL expiration time in seconds
    
    Returns:
        Presigned URL for uploading this part
    """
    s3_client = get_s3_client()
    
    try:
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod='upload_part',
            Params={
                'Bucket': bucket_name,
                'Key': object_key,
                'UploadId': upload_id,
                'PartNumber': part_number
            },
            ExpiresIn=expiration
        )
        return presigned_url
    except ClientError as e:
        raise Exception(f"Failed to generate presigned URL for part {part_number}: {str(e)}")


def complete_multipart_upload(
    bucket_name: str, 
    object_key: str, 
    upload_id: str, 
    parts: List[Dict[str, Any]]
) -> str:
    """
    Complete a multi-part upload
    
    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key
        upload_id: Multi-part upload ID
        parts: List of parts with ETags and PartNumbers
    
    Returns:
        S3 URL of the completed upload
    """
    s3_client = get_s3_client()
    
    try:
        # Sort parts by part number
        sorted_parts = sorted(parts, key=lambda x: x['PartNumber'])
        
        response = s3_client.complete_multipart_upload(
            Bucket=bucket_name,
            Key=object_key,
            UploadId=upload_id,
            MultipartUpload={'Parts': sorted_parts}
        )
        
        return response['Location']  # Returns the S3 URL
    except ClientError as e:
        raise Exception(f"Failed to complete multipart upload: {str(e)}")


def abort_multipart_upload(bucket_name: str, object_key: str, upload_id: str) -> None:
    """
    Abort a multi-part upload
    
    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key
        upload_id: Multi-part upload ID
    """
    s3_client = get_s3_client()
    
    try:
        s3_client.abort_multipart_upload(
            Bucket=bucket_name,
            Key=object_key,
            UploadId=upload_id
        )
    except ClientError as e:
        # Don't raise exception for abort - it might already be aborted
        print(f"Warning: Failed to abort multipart upload: {str(e)}")


def list_multipart_upload_parts(bucket_name: str, object_key: str, upload_id: str) -> List[Dict[str, Any]]:
    """
    List all parts of a multi-part upload
    
    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key
        upload_id: Multi-part upload ID
    
    Returns:
        List of uploaded parts
    """
    s3_client = get_s3_client()
    
    try:
        response = s3_client.list_parts(
            Bucket=bucket_name,
            Key=object_key,
            UploadId=upload_id
        )
        return response.get('Parts', [])
    except ClientError as e:
        raise Exception(f"Failed to list multipart upload parts: {str(e)}")


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


def get_file_size_from_s3(bucket: str, key: str) -> int:
    """
    Get the size of an S3 object (alias for get_s3_file_size)
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
    
    Returns:
        File size in bytes
    """
    return get_s3_file_size(bucket, key)


def get_video_duration_from_s3(bucket: str, key: str) -> float:
    """
    Get the duration of a video file stored in S3
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
    
    Returns:
        Video duration in seconds
    """
    import tempfile
    import os
    from video_processing_utils import get_video_duration_from_s3 as get_duration
    
    # Download file temporarily to get duration
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, os.path.basename(key))
    
    try:
        download_file_from_s3(bucket, key, temp_path)
        duration = get_duration(bucket, key)  # This function already exists in video_processing_utils
        return duration
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)

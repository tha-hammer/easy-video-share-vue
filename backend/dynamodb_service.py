import os
import uuid
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Key

from typing import List, Optional

# Table name from settings or environment
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "easy-video-share-video-metadata")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)


def iso_utc_now() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def create_job_entry(job_id: str, user_id: Optional[str] = None, upload_date: Optional[str] = None, status: str = "QUEUED", created_at: Optional[str] = None, updated_at: Optional[str] = None):
    """
    Create a new job entry in DynamoDB for job status tracking.
    """
    now = iso_utc_now()
    item = {
        "video_id": job_id,
        "user_id": user_id or "anonymous",
        "upload_date": upload_date or now,
        "status": status,
        "created_at": created_at or now,
        "updated_at": updated_at or now,
    }
    table.put_item(Item=item)
    return item


def update_job_status(job_id: str, status: str, output_s3_urls: Optional[List[str]] = None, error_message: Optional[str] = None, updated_at: Optional[str] = None):
    """
    Update job status and optionally output URLs or error message.
    """
    update_expr = ["#s = :s", "updated_at = :u"]
    expr_attr_names = {"#s": "status"}
    expr_attr_values = {":s": status, ":u": updated_at or iso_utc_now()}
    
    if output_s3_urls is not None:
        update_expr.append("output_s3_urls = :o")
        expr_attr_values[":o"] = output_s3_urls
    if error_message is not None:
        update_expr.append("error_message = :e")
        expr_attr_values[":e"] = error_message
    
    update_expression = "SET " + ", ".join(update_expr)
    
    table.update_item(
        Key={"video_id": job_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values
    )


def get_job_status(job_id: str) -> Optional[dict]:
    """
    Retrieve job status and metadata from DynamoDB.
    """
    resp = table.get_item(Key={"video_id": job_id})
    return resp.get("Item")

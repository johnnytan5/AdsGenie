"""
S3 client and utilities.
"""
import boto3
from botocore.config import Config
from typing import Optional, BinaryIO
from datetime import datetime, timezone

from app.core.config import settings


def get_s3_client():
    """Get S3 client."""
    config = Config(
        region_name=settings.AWS_REGION,
    )

    client_kwargs = {
        "config": config,
    }

    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

    if settings.S3_ENDPOINT_URL:
        client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

    return boto3.client("s3", **client_kwargs)


def upload_file_to_s3(
    file_content: bytes,
    s3_key: str,
    content_type: Optional[str] = None,
) -> str:
    """
    Upload a file to S3.

    Args:
        file_content: File content as bytes
        s3_key: S3 key (path) for the file
        content_type: MIME type of the file

    Returns:
        S3 URL of the uploaded file
    """
    s3_client = get_s3_client()
    extra_args = {}
    if content_type:
        extra_args["ContentType"] = content_type

    s3_client.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=s3_key,
        Body=file_content,
        **extra_args,
    )

    # Generate S3 URL
    if settings.S3_ENDPOINT_URL:
        # Local development or custom endpoint
        return f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{s3_key}"
    else:
        # AWS S3
        return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"


def delete_file_from_s3(s3_key: str) -> None:
    """
    Delete a file from S3.

    Args:
        s3_key: S3 key (path) of the file to delete
    """
    s3_client = get_s3_client()
    s3_client.delete_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=s3_key,
    )


def delete_prefix_from_s3(prefix: str) -> None:
    """
    Delete all files with a given prefix from S3.

    Args:
        prefix: S3 key prefix
    """
    s3_client = get_s3_client()
    paginator = s3_client.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=settings.S3_BUCKET_NAME, Prefix=prefix):
        if "Contents" in page:
            objects = [{"Key": obj["Key"]} for obj in page["Contents"]]
            if objects:
                s3_client.delete_objects(
                    Bucket=settings.S3_BUCKET_NAME,
                    Delete={"Objects": objects},
                )


def generate_s3_key(project_id: str, file_type: str, scene_id: Optional[str] = None) -> str:
    """
    Generate S3 key based on file type and location.

    Args:
        project_id: Project ID
        file_type: Type of file (e.g., 'character_sketch', 'scene_generated_image')
        scene_id: Optional scene ID for scene-specific files

    Returns:
        S3 key path
    """
    if scene_id:
        if file_type == "sketch":
            return f"projects/{project_id}/scenes/{scene_id}/sketch.png"
        elif file_type == "generated_image":
            return f"projects/{project_id}/scenes/{scene_id}/generated_image.png"
        elif file_type == "generated_video":
            return f"projects/{project_id}/scenes/{scene_id}/generated_video.mp4"
    else:
        if file_type == "character_sketch":
            return f"projects/{project_id}/global/character_sketch.png"
        elif file_type == "character_image":
            return f"projects/{project_id}/global/character_image.png"
        elif file_type == "setting_sketch":
            return f"projects/{project_id}/global/setting_sketch.png"
        elif file_type == "setting_image":
            return f"projects/{project_id}/global/setting_image.png"
        elif file_type == "final_video":
            return f"projects/{project_id}/final_video.mp4"

    raise ValueError(f"Unknown file type: {file_type}")

"""
DynamoDB client and configuration.
"""
import boto3
from botocore.config import Config
from typing import Optional

from app.core.config import settings


def get_dynamodb_client():
    """Get DynamoDB client."""
    config = Config(
        region_name=settings.AWS_REGION,
    )

    client_kwargs = {
        "config": config,
    }

    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

    if settings.DYNAMODB_ENDPOINT_URL:
        client_kwargs["endpoint_url"] = settings.DYNAMODB_ENDPOINT_URL

    return boto3.client("dynamodb", **client_kwargs)


def get_dynamodb_resource():
    """Get DynamoDB resource."""
    config = Config(
        region_name=settings.AWS_REGION,
    )

    resource_kwargs = {
        "config": config,
    }

    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        resource_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        resource_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

    if settings.DYNAMODB_ENDPOINT_URL:
        resource_kwargs["endpoint_url"] = settings.DYNAMODB_ENDPOINT_URL

    return boto3.resource("dynamodb", **resource_kwargs)


# Get table reference
def get_projects_table():
    """Get Projects table reference."""
    dynamodb = get_dynamodb_resource()
    return dynamodb.Table(settings.DYNAMODB_TABLE_NAME)

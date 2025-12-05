"""
Application configuration settings.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    PROJECT_NAME: str = "AdsGenie API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AdsGenie Backend API"
    API_V1_STR: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # DynamoDB
    DYNAMODB_TABLE_NAME: str = "Projects"
    DYNAMODB_ENDPOINT_URL: Optional[str] = None  # For local development

    # S3
    S3_BUCKET_NAME: str = "adsgenie-assets"
    S3_ENDPOINT_URL: Optional[str] = None  # For local development

    # AI Services
    NANOBANANA_API_KEY: Optional[str] = None
    NANOBANANA_API_URL: str = "https://api.nanobanana.com/v1"
    VEO3_API_KEY: Optional[str] = None
    VEO3_API_URL: str = "https://api.veo3.com/v1"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

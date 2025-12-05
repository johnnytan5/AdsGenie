"""
Project-related Pydantic schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.global_settings import GlobalCharacter, GlobalSetting
from app.schemas.scene import SceneResponse


class ProjectCreate(BaseModel):
    """Schema for creating a project."""

    name: str = Field(..., min_length=1, max_length=200)
    aspect_ratio: str = Field(..., pattern="^(16:9|9:16)$")


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    aspect_ratio: Optional[str] = Field(None, pattern="^(16:9|9:16)$")


class ProjectResponse(BaseModel):
    """Schema for project response."""

    project_id: str
    name: str
    aspect_ratio: str
    global_character: Optional[GlobalCharacter] = None
    global_setting: Optional[GlobalSetting] = None
    scenes: List[SceneResponse] = []
    final_video_s3_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Schema for project list item."""

    project_id: str
    name: str
    thumbnail_s3_url: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True

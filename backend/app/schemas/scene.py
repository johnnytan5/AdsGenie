"""
Scene-related Pydantic schemas.
"""
from typing import Optional
from pydantic import BaseModel, Field


class SceneCreate(BaseModel):
    """Schema for creating a scene."""

    description: str = Field(..., min_length=1)
    duration: int = Field(..., ge=1, le=60)


class SceneUpdate(BaseModel):
    """Schema for updating a scene."""

    description: Optional[str] = Field(None, min_length=1)
    duration: Optional[int] = Field(None, ge=1, le=60)


class SceneResponse(BaseModel):
    """Schema for scene response."""

    scene_id: str
    order: int
    duration: int
    description: str
    sketch_s3_url: Optional[str] = None
    generated_image_s3_url: Optional[str] = None
    generated_video_s3_url: Optional[str] = None
    status: str = Field(..., pattern="^(pending|processing|done|failed)$")

    class Config:
        from_attributes = True


class SceneReorderItem(BaseModel):
    """Schema for scene reorder item."""

    scene_id: str
    order: int = Field(..., ge=1)


class SceneReorderRequest(BaseModel):
    """Schema for scene reorder request."""

    scene_order: list[SceneReorderItem]

"""
Image and video generation schemas.
"""
from typing import Optional
from pydantic import BaseModel


class ImageGenerationRequest(BaseModel):
    """Schema for image generation request."""

    use_global_character: bool = True
    use_global_setting: bool = True


class ImageGenerationResponse(BaseModel):
    """Schema for image generation response."""

    scene_id: str
    generated_image_s3_url: str
    status: str


class VideoGenerationRequest(BaseModel):
    """Schema for video generation request."""

    aspect_ratio: str = "16:9"
    voiceover_text: Optional[str] = None
    use_global_character: bool = True
    use_global_setting: bool = True


class VideoGenerationResponse(BaseModel):
    """Schema for video generation response."""

    scene_id: str
    generated_video_s3_url: str
    status: str


class FullVideoGenerationRequest(BaseModel):
    """Schema for full project video generation request."""

    aspect_ratio: str = "16:9"


class FullVideoGenerationResponse(BaseModel):
    """Schema for full video generation response."""

    project_id: str
    final_video_s3_url: str
    status: str

"""
Global settings (character and setting) schemas.
"""
from typing import Optional
from pydantic import BaseModel


class GlobalCharacter(BaseModel):
    """Global character schema."""

    description: Optional[str] = None
    sketch_s3_url: Optional[str] = None
    generated_image_s3_url: Optional[str] = None

    class Config:
        from_attributes = True


class GlobalSetting(BaseModel):
    """Global setting schema."""

    description: Optional[str] = None
    sketch_s3_url: Optional[str] = None
    generated_image_s3_url: Optional[str] = None

    class Config:
        from_attributes = True


class GlobalCharacterUpdate(BaseModel):
    """Schema for updating global character."""

    description: Optional[str] = None


class GlobalSettingUpdate(BaseModel):
    """Schema for updating global setting."""

    description: Optional[str] = None


class GlobalUpdateRequest(BaseModel):
    """Schema for updating global character and setting."""

    character: Optional[GlobalCharacterUpdate] = None
    setting: Optional[GlobalSettingUpdate] = None


class GlobalUpdateResponse(BaseModel):
    """Schema for global update response."""

    global_character: Optional[GlobalCharacter] = None
    global_setting: Optional[GlobalSetting] = None

"""
Audio-related Pydantic schemas.
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class AudioGenerationRequest(BaseModel):
    """Schema for audio generation request."""
    
    audio_type: Literal["background_music", "text_to_speech", "both"] = Field(
        ...,
        description="Type of audio to generate: background_music, text_to_speech, or both"
    )
    video_description: str = Field(
        ...,
        min_length=1,
        description="Description of the video to base audio generation on"
    )
    duration: int = Field(
        ...,
        ge=1,
        le=300,
        description="Duration of the audio in seconds"
    )
    tts_text: Optional[str] = Field(
        None,
        description="Text for text-to-speech (required if audio_type is 'text_to_speech' or 'both')"
    )
    voice_id: Optional[str] = Field(
        None,
        description="Optional ElevenLabs voice ID for TTS"
    )


class AudioGenerationResponse(BaseModel):
    """Schema for audio generation response."""
    
    scene_id: Optional[str] = None
    project_id: str
    audio_type: str
    background_music_s3_url: Optional[str] = None
    tts_audio_s3_url: Optional[str] = None
    combined_audio_s3_url: Optional[str] = None
    status: str = Field(..., pattern="^(processing|done|failed)$")


class VideoAudioRequest(BaseModel):
    """Schema for adding audio to a video."""
    
    audio_type: Literal["background_music", "text_to_speech", "both"] = Field(
        ...,
        description="Type of audio to add: background_music, text_to_speech, or both"
    )
    video_description: str = Field(
        ...,
        min_length=1,
        description="Description of the video to base audio generation on"
    )
    tts_text: Optional[str] = Field(
        None,
        description="Text for text-to-speech (required if audio_type is 'text_to_speech' or 'both')"
    )
    voice_id: Optional[str] = Field(
        None,
        description="Optional ElevenLabs voice ID for TTS"
    )


class VideoAudioResponse(BaseModel):
    """Schema for video with audio response."""
    
    scene_id: Optional[str] = None
    project_id: str
    video_with_audio_s3_url: Optional[str] = None
    status: str = Field(..., pattern="^(processing|done|failed)$")


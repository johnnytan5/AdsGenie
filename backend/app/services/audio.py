"""
Audio service for generating music and text-to-speech using ElevenLabs and OpenAI.
"""
import json
import logging
from typing import Optional, Dict, Any
from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_openai_client() -> OpenAI:
    """Get OpenAI client."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    return OpenAI(api_key=settings.OPENAI_API_KEY)


async def determine_music_type(video_description: str) -> Dict[str, Any]:
    """
    Use OpenAI to determine appropriate music type based on video description.
    
    Args:
        video_description: Description of the video content
        
    Returns:
        Dictionary with music_type, mood, and description
    """
    try:
        client = get_openai_client()
        
        prompt = f"""Based on the following video description, determine the most appropriate background music type, mood, and characteristics.

Video Description: {video_description}

Analyze the emotional tone, setting, and context. Return a JSON object with:
- music_type: One of ["sad", "happy", "energetic", "calm", "dramatic", "romantic", "party", "mysterious", "inspiring", "melancholic", "upbeat", "ambient"]
- mood: A brief description of the mood (e.g., "sad and emotional", "energetic and celebratory")
- tempo: One of ["slow", "medium", "fast"]
- instruments: Suggested instruments (e.g., "piano, strings", "drums, electric guitar")
- description: A detailed prompt for generating this type of music

Example response:
{{
    "music_type": "sad",
    "mood": "sad and emotional",
    "tempo": "slow",
    "instruments": "piano, strings",
    "description": "A slow, melancholic piece with soft piano and gentle strings, conveying sadness and emotion"
}}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a music expert that analyzes video descriptions and recommends appropriate background music. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        
        result = response.choices[0].message.content
        music_info = json.loads(result)
        
        logger.info(f"Determined music type: {music_info.get('music_type')} for description: {video_description[:50]}...")
        return music_info
        
    except Exception as e:
        logger.error(f"Error determining music type: {str(e)}")
        # Return default music type
        return {
            "music_type": "ambient",
            "mood": "neutral",
            "tempo": "medium",
            "instruments": "synthesizer",
            "description": "Ambient background music"
        }


async def generate_background_music(
    video_description: str,
    duration: int,
    music_info: Optional[Dict[str, Any]] = None
) -> Optional[bytes]:
    """
    Generate background music based on video description and duration.
    
    Args:
        video_description: Description of the video
        duration: Duration in seconds
        music_info: Optional pre-determined music info from OpenAI
        
    Returns:
        Audio bytes or None if failed
    """
    try:
        # Determine music type if not provided
        if not music_info:
            music_info = await determine_music_type(video_description)
        
        # Import ElevenLabs service
        from app.services.elevenlabs import ElevenLabsService
        
        elevenlabs_service = ElevenLabsService()
        
        # Generate music using ElevenLabs Sound Effects API
        music_bytes = elevenlabs_service.generate_music(
            description=music_info.get("description", video_description),
            duration=duration,
            music_type=music_info.get("music_type"),
            mood=music_info.get("mood"),
            tempo=music_info.get("tempo"),
            instruments=music_info.get("instruments")
        )
        
        if music_bytes:
            logger.info(f"Successfully generated {duration}s of background music")
            return music_bytes
        
        # If ElevenLabs doesn't support music generation, return None
        # In production, you might want to integrate with another music generation service
        logger.warning("Music generation not available via ElevenLabs. Consider integrating alternative service.")
        return None
        
    except Exception as e:
        logger.error(f"Error generating background music: {str(e)}")
        return None


async def generate_text_to_speech(
    text: str,
    voice_id: Optional[str] = None
) -> Optional[bytes]:
    """
    Generate text-to-speech audio using ElevenLabs.
    
    Args:
        text: Text to convert to speech
        voice_id: Optional voice ID
        
    Returns:
        Audio bytes or None if failed
    """
    try:
        # Import ElevenLabs service
        from app.services.elevenlabs import ElevenLabsService
        
        elevenlabs_service = ElevenLabsService()
        
        audio_bytes = elevenlabs_service.generate_audio_bytes(text, voice_id)
        
        if audio_bytes:
            logger.info(f"Successfully generated TTS audio for text: {text[:50]}...")
            return audio_bytes
        
        return None
        
    except Exception as e:
        logger.error(f"Error generating text-to-speech: {str(e)}")
        return None


async def combine_audio_tracks(
    background_music: bytes,
    tts_audio: bytes,
    music_volume: float = 0.3,
    tts_volume: float = 1.0
) -> Optional[bytes]:
    """
    Combine background music and TTS audio tracks.
    
    Args:
        background_music: Background music audio bytes
        tts_audio: Text-to-speech audio bytes
        music_volume: Volume level for background music (0.0-1.0)
        tts_volume: Volume level for TTS (0.0-1.0)
        
    Returns:
        Combined audio bytes or None if failed
    """
    try:
        # This would typically use FFmpeg or similar to mix audio
        # For now, return None - this needs to be implemented with audio processing library
        logger.warning("Audio mixing not yet implemented. Requires FFmpeg or similar.")
        return None
        
    except Exception as e:
        logger.error(f"Error combining audio tracks: {str(e)}")
        return None


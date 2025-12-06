"""
ElevenLabs service wrapper for backend use.
"""
import requests
import logging
from typing import Optional, Dict, Any
import os

from app.core.config import settings

logger = logging.getLogger(__name__)


class ElevenLabsService:
    """Service for ElevenLabs Text-to-Speech and Music integration"""
    
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY or os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        self.default_voice_id = settings.ELEVENLABS_VOICE_ID or os.getenv("ELEVENLABS_VOICE_ID", "yj4ZLC16WtrBEwPzIXzI")
        self.headers = {
            'xi-api-key': self.api_key,
            'Content-Type': 'application/json'
        } if self.api_key else {}
    
    def generate_audio_bytes(self, text: str, voice_id: Optional[str] = None) -> Optional[bytes]:
        """
        Generate audio from text using ElevenLabs TTS and return raw bytes.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use (optional, uses default if not provided)
            
        Returns:
            Audio bytes or None if failed
        """
        if not self.api_key:
            logger.warning("ElevenLabs API key not found. Audio generation disabled.")
            return None
        
        try:
            voice = voice_id or self.default_voice_id
            url = f"{self.base_url}/text-to-speech/{voice}"
            
            data = {
                "text": text,
                "voice_settings": {
                    "stability": 0.75,
                    "clarity": 0.9,
                    "similarity_boost": 0.8
                }
            }
            
            logger.info(f"Generating audio bytes for text: {text[:100]}...")
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 200:
                logger.info("Successfully generated audio bytes with ElevenLabs")
                return response.content
            else:
                logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating audio bytes: {str(e)}")
            return None
    
    def _create_music_prompt(
        self,
        description: str,
        music_type: Optional[str] = None,
        mood: Optional[str] = None,
        tempo: Optional[str] = None,
        instruments: Optional[str] = None
    ) -> str:
        """
        Create a prompt for ElevenLabs Sound Effects API based on music requirements.
        
        Args:
            description: Video description
            music_type: Music type (e.g., "sad", "happy", "party")
            mood: Mood description
            tempo: Tempo (slow, medium, fast)
            instruments: Suggested instruments
            
        Returns:
            Formatted prompt string for sound effects API
        """
        # Build prompt based on available information
        prompt_parts = []
        
        if music_type:
            # Map music types to descriptive prompts
            music_prompts = {
                "sad": "melancholic, emotional, somber",
                "happy": "upbeat, cheerful, joyful",
                "energetic": "energetic, dynamic, powerful",
                "calm": "calm, peaceful, serene",
                "dramatic": "dramatic, intense, cinematic",
                "romantic": "romantic, soft, tender",
                "party": "upbeat dance music, celebratory, festive",
                "mysterious": "mysterious, suspenseful, atmospheric",
                "inspiring": "inspiring, uplifting, motivational",
                "melancholic": "melancholic, wistful, nostalgic",
                "upbeat": "upbeat, lively, energetic",
                "ambient": "ambient, atmospheric, background"
            }
            prompt_parts.append(music_prompts.get(music_type, music_type))
        
        if tempo:
            tempo_descriptions = {
                "slow": "slow tempo",
                "medium": "medium tempo",
                "fast": "fast tempo"
            }
            prompt_parts.append(tempo_descriptions.get(tempo, tempo))
        
        if instruments:
            prompt_parts.append(f"with {instruments}")
        
        # Add mood if provided
        if mood:
            prompt_parts.append(f"mood: {mood}")
        
        # Build final prompt
        if prompt_parts:
            prompt = ", ".join(prompt_parts) + " background music"
        else:
            # Fallback: use description to create prompt
            prompt = f"background music for: {description}"
        
        return prompt
    
    def generate_music(
        self, 
        description: str, 
        duration: int,
        music_type: Optional[str] = None,
        mood: Optional[str] = None,
        tempo: Optional[str] = None,
        instruments: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Generate background music using ElevenLabs Sound Effects API.
        
        Uses the text-to-sound-effects endpoint to generate music based on
        video description and music characteristics.
        
        Note: ElevenLabs also has an "Eleven Music API" which may be more
        suitable for music generation. Consider switching to that if available.
        See: https://elevenlabs.io/blog/eleven-music-now-available-in-the-api
        
        Reference: https://elevenlabs.io/docs/developers/guides/cookbooks/sound-effects
        
        Args:
            description: Video description to base music on
            duration: Duration in seconds (will be used to determine looping)
            music_type: Optional music type/style (e.g., "sad", "happy", "party")
            mood: Optional mood description
            tempo: Optional tempo (slow, medium, fast)
            instruments: Optional suggested instruments
            
        Returns:
            Audio bytes or None if failed
        """
        if not self.api_key:
            logger.warning("ElevenLabs API key not found. Music generation disabled.")
            return None
        
        try:
            # Create prompt for sound effects API
            prompt = self._create_music_prompt(
                description=description,
                music_type=music_type,
                mood=mood,
                tempo=tempo,
                instruments=instruments
            )
            
            # Try ElevenLabs Music API first (for music generation)
            # Endpoint: /v1/music/compose
            # Reference: https://elevenlabs.io/docs/api-reference/music-compose
            url = f"{self.base_url}/music/compose"
            
            # Prepare request data for Music API
            # - prompt: The text description of the music
            # - music_length_ms: Duration in milliseconds
            data = {
                "prompt": prompt,
                "music_length_ms": duration * 1000  # Convert seconds to milliseconds
            }
            
            logger.info(f"Generating music with Music API: {prompt[:100]}... (duration: {duration}s)")
            response = requests.post(url, headers=self.headers, json=data, timeout=120)
            
            # If Music API works, return the result
            if response.status_code == 200:
                audio_bytes = response.content
                logger.info(f"Successfully generated {len(audio_bytes)} bytes of music with ElevenLabs Music API")
                return audio_bytes
            
            # If Music API returns 404, try Sound Effects API as fallback
            if response.status_code == 404:
                logger.info("Music API not available, trying Sound Effects API as fallback...")
                url = f"{self.base_url}/text-to-sound-effects"
                
                # Prepare request data for Sound Effects API
                data = {
                    "text": prompt
                }
                
                # Add optional parameters if supported
                if duration <= 30:  # Only set if within typical limits
                    data["duration_seconds"] = duration
                
                data["prompt_influence"] = 0.5
                
                response = requests.post(url, headers=self.headers, json=data, timeout=60)
                
                if response.status_code == 200:
                    audio_bytes = response.content
                    logger.info(f"Successfully generated {len(audio_bytes)} bytes with Sound Effects API")
                    return audio_bytes
                else:
                    logger.error(f"Sound Effects API error: {response.status_code} - {response.text}")
                    return None
            else:
                logger.error(f"ElevenLabs Music API error: {response.status_code} - {response.text}")
                return None
            
            if response.status_code == 200:
                audio_bytes = response.content
                logger.info(f"Successfully generated {len(audio_bytes)} bytes of music with ElevenLabs")
                
                # If duration is longer than what we generated, we might need to loop
                # For now, return what we got - looping can be handled in post-processing
                return audio_bytes
            else:
                logger.error(f"ElevenLabs Sound Effects API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"ElevenLabs Sound Effects API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in music generation: {str(e)}")
            return None
    
    def get_available_voices(self) -> Optional[Dict[str, Any]]:
        """
        Get list of available voices from ElevenLabs.
        
        Returns:
            Dictionary containing available voices or None if failed
        """
        if not self.api_key:
            logger.warning("ElevenLabs API key not found. Cannot fetch voices.")
            return None
        
        try:
            url = f"{self.base_url}/voices"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                voices_data = response.json()
                logger.info(f"Retrieved {len(voices_data.get('voices', []))} voices from ElevenLabs")
                return voices_data
            else:
                logger.error(f"Failed to fetch voices: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching voices: {str(e)}")
            return None
    
    def get_voice_by_name(self, voice_name: str) -> Optional[str]:
        """
        Get voice ID by voice name.
        
        Args:
            voice_name: Name of the voice to find
            
        Returns:
            Voice ID or None if not found
        """
        voices_data = self.get_available_voices()
        if not voices_data:
            return None
        
        for voice in voices_data.get('voices', []):
            if voice.get('name', '').lower() == voice_name.lower():
                return voice.get('voice_id')
        
        logger.warning(f"Voice '{voice_name}' not found")
        return None
    
    def get_educational_voice_settings(self) -> Dict[str, float]:
        """
        Get voice settings optimized for educational content.
        
        Returns:
            Dictionary with voice settings
        """
        return {
            "stability": 0.75,      # Balanced stability for clarity
            "clarity": 0.9,         # High clarity for educational content
            "similarity_boost": 0.8 # Maintain voice consistency
        }
    
    def get_storytelling_voice_settings(self) -> Dict[str, float]:
        """
        Get voice settings optimized for storytelling content.
        
        Returns:
            Dictionary with voice settings
        """
        return {
            "stability": 0.6,       # More variation for storytelling
            "clarity": 0.85,        # Good clarity but more expressive
            "similarity_boost": 0.7 # Allow more voice variation
        }


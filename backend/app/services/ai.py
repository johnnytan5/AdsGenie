"""
AI service integrations for image and video generation.
"""
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings


async def generate_image_nanobanana(
    description: str,
    sketch_url: Optional[str] = None,
    global_character_url: Optional[str] = None,
    global_setting_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate image using NanoBanana API.

    Args:
        description: Scene description
        sketch_url: Optional sketch image URL
        global_character_url: Optional global character image URL
        global_setting_url: Optional global setting image URL

    Returns:
        Dictionary with generated image URL or error
    """
    if not settings.NANOBANANA_API_KEY:
        raise ValueError("NANOBANANA_API_KEY not configured")

    # Build prompt from description and optional references
    prompt = description
    if global_character_url:
        prompt += f" Character reference: {global_character_url}"
    if global_setting_url:
        prompt += f" Setting reference: {global_setting_url}"

    payload = {
        "prompt": prompt,
        "model": "nanobanana-v1",
    }

    if sketch_url:
        payload["sketch_url"] = sketch_url

    headers = {
        "Authorization": f"Bearer {settings.NANOBANANA_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.NANOBANANA_API_URL}/generate",
                json=payload,
                headers=headers,
                timeout=300.0,  # 5 minutes timeout for image generation
            )
            response.raise_for_status()
            result = response.json()
            return {
                "success": True,
                "image_url": result.get("image_url"),
            }
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": str(e),
            }


async def generate_video_veo3(
    image_url: str,
    aspect_ratio: str = "16:9",
    voiceover_text: Optional[str] = None,
    duration: int = 5,
) -> Dict[str, Any]:
    """
    Generate video using VEO3.1 API.

    Args:
        image_url: Source image URL
        aspect_ratio: Video aspect ratio (16:9 or 9:16)
        voiceover_text: Optional voiceover text
        duration: Video duration in seconds

    Returns:
        Dictionary with generated video URL or error
    """
    if not settings.VEO3_API_KEY:
        raise ValueError("VEO3_API_KEY not configured")

    payload = {
        "image_url": image_url,
        "aspect_ratio": aspect_ratio,
        "duration": duration,
    }

    if voiceover_text:
        payload["voiceover_text"] = voiceover_text

    headers = {
        "Authorization": f"Bearer {settings.VEO3_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.VEO3_API_URL}/generate",
                json=payload,
                headers=headers,
                timeout=600.0,  # 10 minutes timeout for video generation
            )
            response.raise_for_status()
            result = response.json()
            return {
                "success": True,
                "video_url": result.get("video_url"),
            }
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": str(e),
            }

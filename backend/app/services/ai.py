"""
AI service integrations for image and video generation using Google GenAI SDK.
"""
import asyncio
import time
import tempfile
import os
from typing import Optional, Dict, Any, List
from io import BytesIO
from PIL import Image
import httpx

from google import genai
from google.genai import types

from app.core.config import settings


def get_genai_client() -> genai.Client:
    """Get Google GenAI client."""
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not configured")
    return genai.Client(api_key=settings.GOOGLE_API_KEY)


async def download_image(url: str) -> Image.Image:
    """Download image from URL and return PIL Image.
    
    Handles both S3 URLs (using boto3) and regular HTTP URLs.
    """
    from app.core.s3 import extract_s3_key_from_url, download_file_from_s3
    from app.core.config import settings
    
    # Check if it's an S3 URL
    if settings.S3_BUCKET_NAME in url:
        s3_key = extract_s3_key_from_url(url)
        if s3_key:
            # Download from S3 using boto3
            image_bytes = download_file_from_s3(s3_key)
            return Image.open(BytesIO(image_bytes))
    
    # Otherwise, download via HTTP
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=60.0)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))


async def generate_image_nanobanana(
    description: str,
    sketch_url: Optional[str] = None,
    global_character_url: Optional[str] = None,
    global_setting_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate image using NanoBanana (Gemini 2.5 Flash Image).
    
    Uses text-and-image-to-image if sketch is provided, otherwise falls back to text-to-image.
    
    Args:
        description: Scene description (text prompt)
        sketch_url: Optional sketch image URL (base image for editing)
        global_character_url: Optional global character image URL (for reference)
        global_setting_url: Optional global setting image URL (for reference)
    
    Returns:
        Dictionary with generated image bytes or error
    """
    try:
        client = get_genai_client()
        
        # Build prompt with optional references
        prompt = description
        if global_character_url:
            prompt += f" Maintain character consistency with the provided character reference."
        if global_setting_url:
            prompt += f" Maintain setting consistency with the provided setting reference."
        
        # Prepare contents list
        contents = [prompt]
        
        # Add sketch image if provided (for image editing)
        if sketch_url:
            sketch_image = await download_image(sketch_url)
            contents.append(sketch_image)
        
        # Add reference images if provided (for style/character consistency)
        if global_character_url:
            character_image = await download_image(global_character_url)
            contents.append(character_image)
        
        if global_setting_url:
            setting_image = await download_image(global_setting_url)
            contents.append(setting_image)
        
        # Generate image
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=contents,
        )
        
        # Extract generated image
        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                
                # Convert to bytes - Google GenAI image might need special handling
                # Try saving to temp file first, then read as bytes (most reliable method)
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    tmp_path = tmp_file.name
                
                try:
                    # Save to file (this works according to the guide)
                    image.save(tmp_path)
                    # Read the file back as bytes
                    with open(tmp_path, 'rb') as f:
                        image_bytes = f.read()
                finally:
                    # Clean up temp file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                
                return {
                    "success": True,
                    "image_bytes": image_bytes,
                }
        
        return {
            "success": False,
            "error": "No image generated in response",
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def generate_image_gemini3_pro(
    description: str,
    aspect_ratio: str = "16:9",
    sketch_url: Optional[str] = None,
    global_character_url: Optional[str] = None,
    global_setting_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate image using Gemini 3 Pro Preview with multi-image support.
    
    Supports up to 14 reference images (up to 6 objects, up to 5 humans).
    
    Args:
        description: Image description (text prompt)
        aspect_ratio: Aspect ratio for the generated image (e.g., "16:9", "1:1")
        sketch_url: Optional sketch image URL (object reference)
        global_character_url: Optional global character image URL (human reference)
        global_setting_url: Optional global setting image URL (object reference)
    
    Returns:
        Dictionary with generated image bytes or error
    """
    try:
        client = get_genai_client()
        
        # Prepare contents list with prompt
        contents = [description]
        
        # Add reference images (up to 14 total: 6 objects, 5 humans)
        reference_images = []
        
        # Add sketch if provided (object reference)
        if sketch_url:
            sketch_image = await download_image(sketch_url)
            reference_images.append(sketch_image)
        
        # Add global character if provided (human reference)
        if global_character_url:
            character_image = await download_image(global_character_url)
            reference_images.append(character_image)
        
        # Add global setting if provided (object reference)
        if global_setting_url:
            setting_image = await download_image(global_setting_url)
            reference_images.append(setting_image)
        
        # Add all reference images to contents
        contents.extend(reference_images)
        
        # Generate image with Gemini 3 Pro Preview
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE'],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size="2K",  # Fixed to 2K as per requirements
                ),
            ),
        )
        
        # Extract generated image
        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                
                # Convert to bytes - save to temp file first, then read as bytes
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    tmp_path = tmp_file.name
                
                try:
                    # Save to file
                    image.save(tmp_path)
                    # Read the file back as bytes
                    with open(tmp_path, 'rb') as f:
                        image_bytes = f.read()
                finally:
                    # Clean up temp file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                
                return {
                    "success": True,
                    "image_bytes": image_bytes,
                }
        
        return {
            "success": False,
            "error": "No image generated in response",
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def generate_video_veo3(
    scene_image_url: str,
    aspect_ratio: str = "16:9",
    voiceover_text: Optional[str] = None,
    use_global_character: bool = False,
    use_global_setting: bool = False,
    global_character_url: Optional[str] = None,
    global_setting_url: Optional[str] = None,
    prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate video using VEO 3.1 with reference images.
    
    Args:
        scene_image_url: Scene generated image URL (required - main image)
        aspect_ratio: Video aspect ratio (16:9 or 9:16)
        voiceover_text: Optional voiceover text
        use_global_character: Whether to use global character as reference
        use_global_setting: Whether to use global setting as reference
        global_character_url: Optional global character image URL
        global_setting_url: Optional global setting image URL
        prompt: Optional custom prompt (if not provided, will use scene description)
    
    Returns:
        Dictionary with generated video bytes or error
    """
    try:
        client = get_genai_client()
        
        # Download scene image (required)
        scene_image = await download_image(scene_image_url)
        
        # Build reference images list (up to 3)
        reference_images = []
        
        # Add global character if requested and available
        if use_global_character and global_character_url:
            character_image = await download_image(global_character_url)
            reference_images.append(
                types.VideoGenerationReferenceImage(
                    image=character_image,
                    reference_type="asset"
                )
            )
        
        # Add global setting if requested and available
        if use_global_setting and global_setting_url:
            setting_image = await download_image(global_setting_url)
            reference_images.append(
                types.VideoGenerationReferenceImage(
                    image=setting_image,
                    reference_type="asset"
                )
            )
        
        # Build prompt
        video_prompt = prompt or "Create a cinematic video based on this scene."
        if voiceover_text:
            video_prompt += f" Include dialogue: {voiceover_text}"
        
        # Prepare config with reference images if available
        config = None
        if reference_images:
            config = types.GenerateVideosConfig(
                reference_images=reference_images
            )
        
        # Generate video (this is an async operation)
        # Scene image is passed as the main image parameter
        # Global character/setting are passed as reference images in config
        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=video_prompt,
            image=scene_image,
            config=config,
        )
        
        # Poll the operation status until the video is ready
        max_wait_time = 600  # 10 minutes max
        wait_interval = 10  # Check every 10 seconds
        elapsed_time = 0
        
        while not operation.done and elapsed_time < max_wait_time:
            await asyncio.sleep(wait_interval)
            elapsed_time += wait_interval
            operation = client.operations.get(operation)
        
        if not operation.done:
            return {
                "success": False,
                "error": "Video generation timed out",
            }
        
        if operation.error:
            return {
                "success": False,
                "error": str(operation.error),
            }
        
        # Download the generated video
        generated_video = operation.response.generated_videos[0]
        
        # Download the file - this returns a file object
        video_file_obj = client.files.download(file=generated_video.video)
        
        # Save to temporary bytes buffer
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            video_file_obj.save(tmp_file.name)
            with open(tmp_file.name, 'rb') as f:
                video_bytes = f.read()
            os.unlink(tmp_file.name)  # Clean up temp file
        
        return {
            "success": True,
            "video_bytes": video_bytes,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }

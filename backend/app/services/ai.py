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
    duration: int = 8,
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
        duration: Video duration in seconds (4, 6, or 8 for Veo 3.1). Default is 8.
                  Note: When using reference images, duration may be fixed at 8 seconds.
    
    Returns:
        Dictionary with generated video bytes or error
    """
    try:
        client = get_genai_client()
        
        # Helper function to convert PIL Image to GenAI Image
        def pil_to_genai_image(pil_image: Image.Image) -> types.Image:
            """Convert PIL Image to GenAI Image type."""
            # Convert PIL Image to bytes
            buffer = BytesIO()
            pil_image.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
            
            # Create GenAI Image with imageBytes and mimeType
            return types.Image(
                imageBytes=image_bytes,
                mimeType='image/png'
            )
        
        # Download scene image (required) and convert to GenAI Image type
        scene_image_pil = await download_image(scene_image_url)
        scene_image = pil_to_genai_image(scene_image_pil)
        
        # Build reference images list (up to 3)
        reference_images = []
        
        # Add global character if requested and available
        if use_global_character and global_character_url:
            character_image_pil = await download_image(global_character_url)
            character_image = pil_to_genai_image(character_image_pil)
            reference_images.append(
                types.VideoGenerationReferenceImage(
                    image=character_image,
                    reference_type="asset"
                )
            )
        
        # Add global setting if requested and available
        if use_global_setting and global_setting_url:
            setting_image_pil = await download_image(global_setting_url)
            setting_image = pil_to_genai_image(setting_image_pil)
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
        
        # Validate and normalize duration for Veo 3.1 (must be 4, 6, or 8 seconds)
        # Note: When using reference images, duration may be fixed at 8 seconds
        valid_durations = [4, 6, 8]
        original_duration = duration
        if duration not in valid_durations:
            # Default to 6 seconds if duration is not valid
            duration = 6
            print(f"[VIDEO GENERATION] Duration {original_duration} not valid for Veo 3.1, defaulting to 6 seconds. Valid values: {valid_durations}")
        
        # Prepare config with reference images, duration, and aspect ratio
        config_kwargs = {}
        if reference_images:
            config_kwargs["reference_images"] = reference_images
        
        # Add duration to config (Veo 3.1 supports 4, 6, or 8 seconds)
        # Note: When using reference images, duration may be fixed at 8 seconds, but we'll try to set it
        config_kwargs["duration_seconds"] = duration
        
        # Add aspect ratio to config (Veo 3.1 supports "16:9" or "9:16")
        # Convert project aspect ratio to Veo format if needed
        veo_aspect_ratio = aspect_ratio
        if aspect_ratio not in ["16:9", "9:16"]:
            # Map common aspect ratios to Veo-supported ones
            # Default to 16:9 for landscape, 9:16 for portrait
            if "16" in aspect_ratio or "9" in aspect_ratio:
                # If it's a landscape ratio (width > height), use 16:9
                # If it's a portrait ratio (height > width), use 9:16
                # For simplicity, default to 16:9 if unclear
                veo_aspect_ratio = "16:9"
            else:
                veo_aspect_ratio = "16:9"  # Default fallback
        
        config_kwargs["aspect_ratio"] = veo_aspect_ratio
        print(f"[VIDEO GENERATION] Using aspect ratio: {veo_aspect_ratio} (from project: {aspect_ratio})")
        
        # Always create config (even if no reference images, we still want to set duration and aspect ratio)
        config = types.GenerateVideosConfig(**config_kwargs)
        
        # Generate video (this is an async operation)
        # Scene image is passed as the main image parameter
        # Global character/setting are passed as reference images in config
        print(f"[VIDEO GENERATION] Starting video generation with model: veo-3.1-fast-generate-preview")
        print(f"[VIDEO GENERATION] Prompt: {video_prompt[:100]}...")
        print(f"[VIDEO GENERATION] Duration: {duration} seconds")
        print(f"[VIDEO GENERATION] Reference images count: {len(reference_images)}")
        
        operation = client.models.generate_videos(
            model="veo-3.1-fast-generate-preview",  # Using faster and cheaper model
            prompt=video_prompt,
            image=scene_image,
            config=config,
        )
        
        print(f"[VIDEO GENERATION] Operation created: {operation.name}")
        print(f"[VIDEO GENERATION] Starting to poll operation status every 10 seconds...")
        
        # Poll the operation status until the video is ready
        max_wait_time = 600  # 10 minutes max
        wait_interval = 10  # Check every 10 seconds
        elapsed_time = 0
        
        while not operation.done and elapsed_time < max_wait_time:
            print(f"[VIDEO GENERATION] Polling... Elapsed: {elapsed_time}s, Operation done: {operation.done}")
            await asyncio.sleep(wait_interval)
            elapsed_time += wait_interval
            operation = client.operations.get(operation)
            print(f"[VIDEO GENERATION] Operation status after poll: done={operation.done}, error={operation.error if hasattr(operation, 'error') else 'None'}")
        
        if not operation.done:
            print(f"[VIDEO GENERATION] Operation timed out after {elapsed_time} seconds")
            return {
                "success": False,
                "error": "Video generation timed out",
            }
        
        if operation.error:
            print(f"[VIDEO GENERATION] Operation error: {operation.error}")
            return {
                "success": False,
                "error": str(operation.error),
            }
        
        print(f"[VIDEO GENERATION] Operation completed successfully! Downloading video...")
        
        # Download the generated video
        generated_video = operation.response.generated_videos[0]
        print(f"[VIDEO GENERATION] Generated video: {generated_video.video}")
        
        # Download the file - this returns bytes directly
        video_bytes = client.files.download(file=generated_video.video)
        print(f"[VIDEO GENERATION] Video downloaded successfully, size: {len(video_bytes)} bytes")
        
        return {
            "success": True,
            "video_bytes": video_bytes,
        }
        
    except Exception as e:
        print(f"[VIDEO GENERATION] Exception occurred: {type(e).__name__}: {e}")
        import traceback
        print(f"[VIDEO GENERATION] Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
        }

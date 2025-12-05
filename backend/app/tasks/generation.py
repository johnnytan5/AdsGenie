"""
Background tasks for image and video generation.
"""
from fastapi import BackgroundTasks
from typing import Optional

from app.crud.project import (
    update_scene_status,
    update_scene_generated_image,
    update_scene_generated_video,
    update_final_video,
    get_project,
)
from app.services.ai import generate_image_nanobanana, generate_video_veo3
from app.core.s3 import upload_file_to_s3, generate_s3_key
import httpx


async def generate_scene_image_task(
    project_id: str,
    scene_id: str,
    description: str,
    sketch_s3_url: Optional[str],
    use_global_character: bool,
    use_global_setting: bool,
) -> None:
    """
    Background task to generate image for a scene.

    Args:
        project_id: Project ID
        scene_id: Scene ID
        description: Scene description
        sketch_s3_url: Optional sketch S3 URL
        use_global_character: Whether to use global character
        use_global_setting: Whether to use global setting
    """
    # Update status to processing
    update_scene_status(project_id, scene_id, "processing")

    try:
        # Get project to access global settings
        project = get_project(project_id)
        if not project:
            update_scene_status(project_id, scene_id, "failed")
            return

        global_character = project.get("global_character")
        global_setting = project.get("global_setting")

        global_character_url = None
        global_setting_url = None

        if use_global_character and global_character:
            global_character_url = global_character.get("generated_image_s3_url")

        if use_global_setting and global_setting:
            global_setting_url = global_setting.get("generated_image_s3_url")

        # Generate image using NanoBanana
        result = await generate_image_nanobanana(
            description=description,
            sketch_url=sketch_s3_url,
            global_character_url=global_character_url,
            global_setting_url=global_setting_url,
        )

        if result.get("success") and result.get("image_url"):
            # Download generated image
            async with httpx.AsyncClient() as client:
                response = await client.get(result["image_url"])
                image_content = response.content

            # Upload to S3
            s3_key = generate_s3_key(project_id, "generated_image", scene_id)
            s3_url = upload_file_to_s3(image_content, s3_key, content_type="image/png")

            # Update scene with generated image URL
            update_scene_generated_image(project_id, scene_id, s3_url)
        else:
            update_scene_status(project_id, scene_id, "failed")

    except Exception as e:
        update_scene_status(project_id, scene_id, "failed")


async def generate_scene_video_task(
    project_id: str,
    scene_id: str,
    image_s3_url: str,
    aspect_ratio: str,
    voiceover_text: Optional[str],
    duration: int,
) -> None:
    """
    Background task to generate video for a scene.

    Args:
        project_id: Project ID
        scene_id: Scene ID
        image_s3_url: Scene image S3 URL
        aspect_ratio: Video aspect ratio
        voiceover_text: Optional voiceover text
        duration: Video duration
    """
    # Update status to processing
    update_scene_status(project_id, scene_id, "processing")

    try:
        # Generate video using VEO3
        result = await generate_video_veo3(
            image_url=image_s3_url,
            aspect_ratio=aspect_ratio,
            voiceover_text=voiceover_text,
            duration=duration,
        )

        if result.get("success") and result.get("video_url"):
            # Download generated video
            async with httpx.AsyncClient() as client:
                response = await client.get(result["video_url"])
                video_content = response.content

            # Upload to S3
            s3_key = generate_s3_key(project_id, "generated_video", scene_id)
            s3_url = upload_file_to_s3(video_content, s3_key, content_type="video/mp4")

            # Update scene with generated video URL
            update_scene_generated_video(project_id, scene_id, s3_url)
        else:
            update_scene_status(project_id, scene_id, "failed")

    except Exception as e:
        update_scene_status(project_id, scene_id, "failed")


async def generate_full_video_task(
    project_id: str,
    aspect_ratio: str,
) -> None:
    """
    Background task to generate full project video.

    Args:
        project_id: Project ID
        aspect_ratio: Video aspect ratio
    """
    try:
        project = get_project(project_id)
        if not project:
            return

        scenes = project.get("scenes", [])
        if not scenes:
            return

        # Ensure all scenes have generated images
        for scene in scenes:
            if not scene.get("generated_image_s3_url"):
                # Generate image first if missing
                await generate_scene_image_task(
                    project_id=project_id,
                    scene_id=scene["scene_id"],
                    description=scene["description"],
                    sketch_s3_url=scene.get("sketch_s3_url"),
                    use_global_character=True,
                    use_global_setting=True,
                )

        # Generate videos for scenes that don't have them
        for scene in scenes:
            if not scene.get("generated_video_s3_url") and scene.get("generated_image_s3_url"):
                await generate_scene_video_task(
                    project_id=project_id,
                    scene_id=scene["scene_id"],
                    image_s3_url=scene["generated_image_s3_url"],
                    aspect_ratio=aspect_ratio,
                    voiceover_text=None,
                    duration=scene.get("duration", 5),
                )

        # Stitch videos together
        # This is a placeholder - you'd implement actual video stitching
        # For now, we'll use the first scene's video as placeholder
        video_urls = [s.get("generated_video_s3_url") for s in scenes if s.get("generated_video_s3_url")]
        if video_urls:
            # In production, stitch videos using FFmpeg
            # For now, use first video as placeholder
            final_video_url = video_urls[0]  # Placeholder
            update_final_video(project_id, final_video_url)

    except Exception as e:
        # Handle error
        pass

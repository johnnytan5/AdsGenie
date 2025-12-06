"""
Background tasks for image and video generation.
"""
from typing import Optional

from app.crud.project import (
    update_scene_status,
    update_scene_generated_image,
    update_scene_generated_video,
    update_final_video,
    get_project,
    update_global_character_s3_urls,
    update_global_setting_s3_urls,
)
from app.services.ai import generate_image_nanobanana, generate_image_gemini3_pro, generate_video_veo3
from app.core.s3 import upload_file_to_s3, generate_s3_key, get_presigned_url_from_s3_url, delete_file_from_s3, extract_s3_key_from_url
from app.core.webhook import send_webhook


async def generate_global_character_image_task(
    project_id: str,
    description: str,
    sketch_s3_url: str,
) -> None:
    """
    Background task to generate image for global character.

    Args:
        project_id: Project ID
        description: Character description
        sketch_s3_url: Sketch S3 URL (can be empty string for text-only generation)
    """
    print(f"[BACKGROUND TASK] Starting character image generation for project {project_id}")
    print(f"[BACKGROUND TASK] Description: {description[:100]}")
    print(f"[BACKGROUND TASK] Sketch URL: {sketch_s3_url or 'None'}")
    try:
        # Generate image using NanoBanana (text-and-image-to-image or text-to-image)
        print(f"[BACKGROUND TASK] Calling generate_image_nanobanana...")
        result = await generate_image_nanobanana(
            description=description,
            sketch_url=sketch_s3_url if sketch_s3_url else None,
            global_character_url=None,
            global_setting_url=None,
        )
        print(f"[BACKGROUND TASK] Generation result: success={result.get('success')}, error={result.get('error', 'None')}")

        if result.get("success") and result.get("image_bytes"):
            print(f"[BACKGROUND TASK] Image generated successfully, uploading to S3...")
            # Upload generated image directly to S3
            image_bytes = result["image_bytes"]
            s3_key = generate_s3_key(project_id, "character_image")
            s3_url = upload_file_to_s3(image_bytes, s3_key, content_type="image/png")
            print(f"[BACKGROUND TASK] Image uploaded to S3: {s3_url}")

            # Update global character with generated image URL
            update_global_character_s3_urls(project_id, generated_image_s3_url=s3_url)
            print(f"[BACKGROUND TASK] Updated DynamoDB with image URL")
            
            # Send webhook notification
            print(f"[BACKGROUND TASK] Sending webhook notification...")
            webhook_sent = await send_webhook(project_id, "global_character", "done")
            if webhook_sent:
                print(f"[BACKGROUND TASK] Character image generation completed successfully")
            else:
                print(f"[BACKGROUND TASK] Character image generation completed but webhook failed")
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"[BACKGROUND TASK] Image generation failed: {error_msg}")
            # Send webhook with failed status
            await send_webhook(project_id, "global_character", "failed")

    except Exception as e:
        # Log error but don't fail silently
        print(f"Error generating global character image: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        # Send webhook with failed status
        await send_webhook(project_id, "global_character", "failed")


async def generate_global_setting_image_task(
    project_id: str,
    description: str,
    sketch_s3_url: str,
) -> None:
    """
    Background task to generate image for global setting.

    Args:
        project_id: Project ID
        description: Setting description
        sketch_s3_url: Sketch S3 URL (can be empty string for text-only generation)
    """
    print(f"[BACKGROUND TASK] Starting setting image generation for project {project_id}")
    print(f"[BACKGROUND TASK] Description: {description[:100]}")
    print(f"[BACKGROUND TASK] Sketch URL: {sketch_s3_url or 'None'}")
    try:
        # Generate image using NanoBanana (text-and-image-to-image or text-to-image)
        print(f"[BACKGROUND TASK] Calling generate_image_nanobanana...")
        result = await generate_image_nanobanana(
            description=description,
            sketch_url=sketch_s3_url if sketch_s3_url else None,
            global_character_url=None,
            global_setting_url=None,
        )
        print(f"[BACKGROUND TASK] Generation result: success={result.get('success')}, error={result.get('error', 'None')}")

        if result.get("success") and result.get("image_bytes"):
            print(f"[BACKGROUND TASK] Image generated successfully, uploading to S3...")
            # Upload generated image directly to S3
            image_bytes = result["image_bytes"]
            s3_key = generate_s3_key(project_id, "setting_image")
            s3_url = upload_file_to_s3(image_bytes, s3_key, content_type="image/png")
            print(f"[BACKGROUND TASK] Image uploaded to S3: {s3_url}")

            # Update global setting with generated image URL
            update_global_setting_s3_urls(project_id, generated_image_s3_url=s3_url)
            print(f"[BACKGROUND TASK] Updated DynamoDB with image URL")
            
            # Send webhook notification
            print(f"[BACKGROUND TASK] Sending webhook notification...")
            webhook_sent = await send_webhook(project_id, "global_setting", "done")
            if webhook_sent:
                print(f"[BACKGROUND TASK] Setting image generation completed successfully")
            else:
                print(f"[BACKGROUND TASK] Setting image generation completed but webhook failed")
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"[BACKGROUND TASK] Image generation failed: {error_msg}")
            # Send webhook with failed status
            await send_webhook(project_id, "global_setting", "failed")

    except Exception as e:
        # Log error but don't fail silently
        print(f"Error generating global setting image: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        # Send webhook with failed status
        await send_webhook(project_id, "global_setting", "failed")


async def generate_scene_image_task(
    project_id: str,
    scene_id: str,
    description: str,
    sketch_s3_url: Optional[str],
    use_global_character: bool = False,
    use_global_setting: bool = False,
    aspect_ratio: str = "16:9",
) -> None:
    """
    Background task to generate image for a scene.
    
    Uses Gemini 3 Pro Preview if global character/setting toggles are enabled,
    otherwise uses NanoBanana (Gemini 2.5 Flash Image).

    Args:
        project_id: Project ID
        scene_id: Scene ID
        description: Image description
        sketch_s3_url: Optional sketch S3 URL
        use_global_character: Whether to use global character image
        use_global_setting: Whether to use global setting image
        aspect_ratio: Project aspect ratio for Gemini 3 Pro
    """
    print(f"[BACKGROUND TASK] Starting scene image generation for project {project_id}, scene {scene_id}")
    print(f"[BACKGROUND TASK] Description: {description[:100] if description else 'None'}")
    print(f"[BACKGROUND TASK] Sketch URL: {sketch_s3_url or 'None'}")
    print(f"[BACKGROUND TASK] Use global character: {use_global_character}, Use global setting: {use_global_setting}")
    
    # Update status to processing
    update_scene_status(project_id, scene_id, "processing")

    try:
        # Get project to access global settings and aspect ratio
        project = get_project(project_id)
        if not project:
            print(f"[BACKGROUND TASK] Project {project_id} not found")
            update_scene_status(project_id, scene_id, "failed")
            await send_webhook(project_id, f"scene_image_{scene_id}", "failed")
            return

        # Use description if valid, otherwise use a default prompt for image generation
        # (sketch is already validated in the endpoint)
        if not description or description.strip() == "" or description == "New Scene":
            # If no valid description but we have a sketch, use a generic prompt
            if sketch_s3_url:
                description = "Generate a high-quality image based on the provided sketch"
                print(f"[BACKGROUND TASK] No valid description provided, using default prompt for sketch-based generation")
            else:
                # This shouldn't happen as endpoint validates, but handle gracefully
                print(f"[BACKGROUND TASK] ERROR: No description or sketch available (should have been validated)")
                update_scene_status(project_id, scene_id, "failed")
                await send_webhook(project_id, f"scene_image_{scene_id}", "failed")
                return

        # Determine which model to use based on toggles
        use_gemini3_pro = use_global_character or use_global_setting
        
        if use_gemini3_pro:
            # Use Gemini 3 Pro Preview with reference images
            print(f"[BACKGROUND TASK] Using Gemini 3 Pro Preview (multi-image support)")
            
            # Get global character and setting URLs if toggles are enabled
            global_character_url = None
            global_setting_url = None
            
            if use_global_character:
                global_character = project.get("global_character")
                if global_character:
                    global_character_url = global_character.get("generated_image_s3_url")
                    print(f"[BACKGROUND TASK] Using global character URL: {global_character_url or 'None'}")
            
            if use_global_setting:
                global_setting = project.get("global_setting")
                if global_setting:
                    global_setting_url = global_setting.get("generated_image_s3_url")
                    print(f"[BACKGROUND TASK] Using global setting URL: {global_setting_url or 'None'}")
            
            # Get project aspect ratio
            project_aspect_ratio = project.get("aspect_ratio", "16:9")
            print(f"[BACKGROUND TASK] Using aspect ratio: {project_aspect_ratio}")
            
            result = await generate_image_gemini3_pro(
                description=description,
                aspect_ratio=project_aspect_ratio,
                sketch_url=sketch_s3_url,
                global_character_url=global_character_url,
                global_setting_url=global_setting_url,
            )
        else:
            # Use NanoBanana (Gemini 2.5 Flash Image) - no global character/setting
            print(f"[BACKGROUND TASK] Using NanoBanana (Gemini 2.5 Flash Image)")
            result = await generate_image_nanobanana(
                description=description,
                sketch_url=sketch_s3_url,
                global_character_url=None,
                global_setting_url=None,
            )
        print(f"[BACKGROUND TASK] Generation result: success={result.get('success')}, error={result.get('error', 'None')}")

        if result.get("success") and result.get("image_bytes"):
            print(f"[BACKGROUND TASK] Image generated successfully, uploading to S3...")
            # Upload generated image directly to S3
            image_bytes = result["image_bytes"]
            s3_key = generate_s3_key(project_id, "generated_image", scene_id)
            s3_url = upload_file_to_s3(image_bytes, s3_key, content_type="image/png")
            print(f"[BACKGROUND TASK] Image uploaded to S3: {s3_url}")

            # Update scene with generated image URL
            update_scene_generated_image(project_id, scene_id, s3_url)
            print(f"[BACKGROUND TASK] Updated DynamoDB with image URL")
            
            # Send webhook notification
            print(f"[BACKGROUND TASK] Sending webhook notification...")
            webhook_sent = await send_webhook(project_id, f"scene_image_{scene_id}", "done")
            if webhook_sent:
                print(f"[BACKGROUND TASK] Scene image generation completed successfully")
            else:
                print(f"[BACKGROUND TASK] Scene image generation completed but webhook failed")
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"[BACKGROUND TASK] Image generation failed: {error_msg}")
            update_scene_status(project_id, scene_id, "failed")
            # Send webhook with failed status
            await send_webhook(project_id, f"scene_image_{scene_id}", "failed")

    except Exception as e:
        # Log error but don't fail silently
        print(f"[BACKGROUND TASK] Error generating scene image: {e}")
        import traceback
        print(f"[BACKGROUND TASK] Traceback: {traceback.format_exc()}")
        update_scene_status(project_id, scene_id, "failed")
        # Send webhook with failed status
        await send_webhook(project_id, f"scene_image_{scene_id}", "failed")


async def generate_scene_video_task(
    project_id: str,
    scene_id: str,
    image_s3_url: str,
    aspect_ratio: str,
    voiceover_text: Optional[str],
    duration: int,
    use_global_character: bool,
    use_global_setting: bool,
) -> None:
    """
    Background task to generate video for a scene.

    Args:
        project_id: Project ID
        scene_id: Scene ID
        image_s3_url: Scene image S3 URL (required)
        aspect_ratio: Video aspect ratio
        voiceover_text: Optional voiceover text
        duration: Video duration (4, 6, or 8 seconds for Veo 3.1)
        use_global_character: Whether to use global character as reference
        use_global_setting: Whether to use global setting as reference
    """
    # Update status to processing
    update_scene_status(project_id, scene_id, "processing")
    
    print(f"[BACKGROUND TASK] Starting scene video generation for project {project_id}, scene {scene_id}")
    print(f"[BACKGROUND TASK] Duration: {duration} seconds")
    print(f"[BACKGROUND TASK] Use global character: {use_global_character}, Use global setting: {use_global_setting}")

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

        # Get scene description for video prompt
        scenes = project.get("scenes", [])
        scene = next((s for s in scenes if s["scene_id"] == scene_id), None)
        scene_description = scene.get("description", "Create a cinematic video based on this scene.") if scene else "Create a cinematic video based on this scene."

        # Generate video using VEO3
        print(f"[BACKGROUND TASK] Generating video with duration: {duration} seconds")
        result = await generate_video_veo3(
            scene_image_url=image_s3_url,
            aspect_ratio=aspect_ratio,
            voiceover_text=voiceover_text,
            use_global_character=use_global_character,
            use_global_setting=use_global_setting,
            global_character_url=global_character_url,
            global_setting_url=global_setting_url,
            prompt=scene_description,
            duration=duration,
        )

        if result.get("success") and result.get("video_bytes"):
            print(f"[BACKGROUND TASK] Video generated successfully, uploading to S3...")
            # Upload generated video directly to S3
            video_bytes = result["video_bytes"]
            s3_key = generate_s3_key(project_id, "generated_video", scene_id)
            s3_url = upload_file_to_s3(video_bytes, s3_key, content_type="video/mp4")
            print(f"[BACKGROUND TASK] Video uploaded to S3: {s3_url}")

            # Get presigned URL for frontend access
            presigned_url = get_presigned_url_from_s3_url(s3_url)
            print(f"[BACKGROUND TASK] Generated presigned URL: {presigned_url}")

            # Update scene with generated video URL
            update_scene_generated_video(project_id, scene_id, s3_url)
            print(f"[BACKGROUND TASK] Updated DynamoDB with video URL")
            
            # Send webhook notification with presigned URL
            print(f"[BACKGROUND TASK] Sending webhook notification with presigned URL...")
            webhook_sent = await send_webhook(project_id, f"scene_video_{scene_id}", "done", presigned_url=presigned_url)
            if webhook_sent:
                print(f"[BACKGROUND TASK] Scene video generation completed successfully")
            else:
                print(f"[BACKGROUND TASK] Scene video generation completed but webhook failed")
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"[BACKGROUND TASK] Video generation failed: {error_msg}")
            print(f"[BACKGROUND TASK] Result: {result}")
            update_scene_status(project_id, scene_id, "failed")
            # Send webhook with failed status
            await send_webhook(project_id, f"scene_video_{scene_id}", "failed")

    except Exception as e:
        # Log error with full traceback
        print(f"[BACKGROUND TASK] Error generating scene video: {e}")
        import traceback
        print(f"[BACKGROUND TASK] Traceback: {traceback.format_exc()}")
        update_scene_status(project_id, scene_id, "failed")
        # Send webhook with failed status
        await send_webhook(project_id, f"scene_video_{scene_id}", "failed")


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

        # Delete existing final video if it exists
        existing_final_video_url = project.get("final_video_s3_url")
        if existing_final_video_url:
            print(f"[GENERATION] Found existing final video: {existing_final_video_url}")
            
            # Only delete if it's actually a final video (not a scene video from old placeholder)
            # Check if the URL contains "final_video" in the path
            s3_key = extract_s3_key_from_url(existing_final_video_url)
            if s3_key and "final_video" in s3_key:
                print(f"[GENERATION] Deleting existing final video from S3: {s3_key}")
                try:
                    delete_file_from_s3(s3_key)
                    print(f"[GENERATION] Successfully deleted final video from S3")
                except Exception as e:
                    print(f"[GENERATION] Error deleting final video from S3: {e}")
            else:
                print(f"[GENERATION] Existing video URL is not a final video (likely old placeholder), skipping S3 deletion")
            
            # Always clear final video URL from DynamoDB (even if it was a placeholder)
            update_final_video(project_id, "")
            print(f"[GENERATION] Cleared final video URL from DynamoDB")
            
            # Send "cleared" webhook to notify frontend
            await send_webhook(project_id, "final_video", "cleared")

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
        print(f"[GENERATION] Checking scene videos for {len(scenes)} scenes...")
        for scene in scenes:
            scene_id = scene["scene_id"]
            if not scene.get("generated_video_s3_url") and scene.get("generated_image_s3_url"):
                print(f"[GENERATION] Generating video for scene {scene_id}...")
                await generate_scene_video_task(
                    project_id=project_id,
                    scene_id=scene_id,
                    image_s3_url=scene["generated_image_s3_url"],
                    aspect_ratio=aspect_ratio,
                    voiceover_text=None,
                    duration=scene.get("duration", 5),
                    use_global_character=True,
                    use_global_setting=True,
                )
                # Refresh scene data after generation
                project = get_project(project_id)
                if project:
                    scenes = project.get("scenes", [])
                    scene = next((s for s in scenes if s["scene_id"] == scene_id), None)
            elif not scene.get("generated_video_s3_url"):
                print(f"[GENERATION] Scene {scene_id} missing generated image, cannot generate video")
            else:
                print(f"[GENERATION] Scene {scene_id} already has video: {scene.get('generated_video_s3_url')}")

        # Stitch videos together using FFmpeg
        video_urls = [s.get("generated_video_s3_url") for s in scenes if s.get("generated_video_s3_url")]
        print(f"[GENERATION] Found {len(video_urls)} scene videos to stitch from {len(scenes)} scenes")
        if not video_urls:
            print(f"[GENERATION] No scene videos found. Scene video URLs: {[s.get('generated_video_s3_url') for s in scenes]}")
            await send_webhook(project_id, "final_video", "failed")
            return
        
        if video_urls:
            from app.services.video_stitcher import stitch_videos_with_transitions
            
            print(f"[GENERATION] Stitching {len(video_urls)} scene videos together...")
            stitched_video_bytes = await stitch_videos_with_transitions(
                video_s3_urls=video_urls,
                project_id=project_id,
                transition_duration=0.5,
            )
            
            if stitched_video_bytes:
                # Upload stitched video to S3
                final_video_key = f"projects/{project_id}/final_video.mp4"
                final_video_url = upload_file_to_s3(
                    stitched_video_bytes,
                    final_video_key,
                    content_type="video/mp4"
                )
                print(f"[GENERATION] Stitched video uploaded to S3: {final_video_url}")
                
                # Update final video URL in DynamoDB
                update_final_video(project_id, final_video_url)
                
                # Get presigned URL for webhook
                presigned_url = get_presigned_url_from_s3_url(final_video_url)
                
                # Send webhook notification with presigned URL
                await send_webhook(project_id, "final_video", "done", presigned_url=presigned_url)
                print(f"[GENERATION] Full video generation completed for project {project_id}")
            else:
                print(f"[GENERATION] Failed to stitch videos")
                await send_webhook(project_id, "final_video", "failed")

    except Exception as e:
        # Handle error
        print(f"Error generating full video: {e}")
        # Send webhook with failed status
        await send_webhook(project_id, "final_video", "failed")

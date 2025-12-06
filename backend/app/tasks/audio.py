"""
Background tasks for audio generation.
"""
from typing import Optional
import logging

from app.crud.project import (
    get_project,
    update_scene_status,
)
from app.services.audio import (
    generate_background_music,
    generate_text_to_speech,
    determine_music_type,
)
from app.core.s3 import upload_file_to_s3, generate_s3_key, get_presigned_url_from_s3_url
from app.core.webhook import send_webhook
from app.services.video_audio_combiner import combine_video_and_audio

logger = logging.getLogger(__name__)


async def generate_audio_task(
    project_id: str,
    scene_id: str,
    audio_type: str,
    video_description: str,
    duration: int,
    tts_text: Optional[str] = None,
    voice_id: Optional[str] = None,
) -> None:
    """
    Background task to generate audio for a scene.
    
    Args:
        project_id: Project ID
        scene_id: Scene ID
        audio_type: Type of audio ("background_music", "text_to_speech", or "both")
        video_description: Description of the video
        duration: Duration in seconds
        tts_text: Text for text-to-speech (required if audio_type includes TTS)
        voice_id: Optional voice ID for TTS
    """
    logger.info(f"[BACKGROUND TASK] Starting audio generation for scene {scene_id}")
    
    try:
        project = get_project(project_id)
        if not project:
            logger.error(f"Project {project_id} not found")
            await send_webhook(project_id, f"audio_{scene_id}", "failed")
            return

        scenes = project.get("scenes", [])
        scene = next((s for s in scenes if s["scene_id"] == scene_id), None)
        if not scene:
            logger.error(f"Scene {scene_id} not found")
            await send_webhook(project_id, f"audio_{scene_id}", "failed")
            return

        background_music_bytes = None
        tts_audio_bytes = None
        combined_audio_bytes = None

        # Determine music type using OpenAI
        music_info = await determine_music_type(video_description)

        # Generate background music if needed
        if audio_type in ["background_music", "both"]:
            logger.info(f"Generating background music for scene {scene_id}")
            background_music_bytes = await generate_background_music(
                video_description=video_description,
                duration=duration,
                music_info=music_info
            )
            
            if background_music_bytes:
                # Upload background music to S3
                s3_key = generate_s3_key(project_id, "background_music", scene_id)
                s3_url = upload_file_to_s3(
                    background_music_bytes,
                    s3_key,
                    content_type="audio/mpeg"
                )
                logger.info(f"Background music uploaded to S3: {s3_url}")
                # Store in scene metadata (you may need to add this to CRUD)
            else:
                logger.warning("Background music generation failed or not available")

        # Generate TTS if needed
        if audio_type in ["text_to_speech", "both"]:
            if not tts_text:
                logger.error("TTS text is required but not provided")
                await send_webhook(project_id, f"audio_{scene_id}", "failed")
                return

            logger.info(f"Generating TTS audio for scene {scene_id}")
            tts_audio_bytes = await generate_text_to_speech(
                text=tts_text,
                voice_id=voice_id
            )
            
            if tts_audio_bytes:
                # Upload TTS audio to S3
                s3_key = generate_s3_key(project_id, "tts_audio", scene_id)
                s3_url = upload_file_to_s3(
                    tts_audio_bytes,
                    s3_key,
                    content_type="audio/mpeg"
                )
                logger.info(f"TTS audio uploaded to S3: {s3_url}")
            else:
                logger.error("TTS audio generation failed")
                await send_webhook(project_id, f"audio_{scene_id}", "failed")
                return

        # Combine audio tracks if both are generated
        if audio_type == "both" and background_music_bytes and tts_audio_bytes:
            # Note: Audio mixing requires FFmpeg or similar library
            # For now, we'll store both separately
            # In production, you'd use FFmpeg to mix them
            logger.info("Both audio tracks generated. Mixing not yet implemented.")
            # combined_audio_bytes = await combine_audio_tracks(...)

        # Send webhook notification
        await send_webhook(project_id, f"audio_{scene_id}", "done")
        logger.info(f"Audio generation completed for scene {scene_id}")

    except Exception as e:
        logger.error(f"Error generating audio: {str(e)}")
        await send_webhook(project_id, f"audio_{scene_id}", "failed")


async def add_audio_to_video_task(
    project_id: str,
    scene_id: Optional[str],
    video_s3_url: str,
    audio_type: str,
    video_description: str,
    duration: int,
    tts_text: Optional[str] = None,
    voice_id: Optional[str] = None,
    music_type: Optional[str] = None,
    mood: Optional[str] = None,
    tempo: Optional[str] = None,
) -> None:
    """
    Background task to add audio to a video.
    
    Args:
        project_id: Project ID
        scene_id: Scene ID (None for full project video)
        video_s3_url: S3 URL of the video
        audio_type: Type of audio ("background_music", "text_to_speech", or "both")
        video_description: Description of the video
        duration: Duration in seconds
        tts_text: Text for text-to-speech (required if audio_type includes TTS)
        voice_id: Optional voice ID for TTS
    """
    logger.info(f"[BACKGROUND TASK] Adding audio to video for {'scene ' + scene_id if scene_id else 'full project'}")

    try:
        project = get_project(project_id)
        if not project:
            logger.error(f"Project {project_id} not found")
            await send_webhook(project_id, f"video_audio_{scene_id or 'full'}", "failed")
            return

        # Prepare music info - use provided parameters or determine via OpenAI
        music_info = None
        if music_type or mood or tempo:
            # Use provided customization parameters
            music_info = {
                "music_type": music_type,
                "mood": mood,
                "tempo": tempo,
                "description": video_description,
            }
        else:
            # Determine music type using OpenAI if no customization provided
            music_info = await determine_music_type(video_description)

        background_music_bytes = None
        tts_audio_bytes = None

        # Generate background music if needed
        if audio_type in ["background_music", "both"]:
            logger.info("Generating background music")
            background_music_bytes = await generate_background_music(
                video_description=video_description,
                duration=duration,
                music_info=music_info
            )

        # Generate TTS if needed
        if audio_type in ["text_to_speech", "both"]:
            if not tts_text:
                logger.error("TTS text is required but not provided")
                await send_webhook(project_id, f"video_audio_{scene_id or 'full'}", "failed")
                return

            logger.info("Generating TTS audio")
            tts_audio_bytes = await generate_text_to_speech(
                text=tts_text,
                voice_id=voice_id
            )

            if not tts_audio_bytes:
                logger.error("TTS audio generation failed")
                await send_webhook(project_id, f"video_audio_{scene_id or 'full'}", "failed")
                return

        # Combine audio tracks if both are generated
        combined_audio_bytes = None
        if audio_type == "both" and background_music_bytes and tts_audio_bytes:
            # Use TTS as primary, background music as secondary
            # In production, use FFmpeg to properly mix them
            combined_audio_bytes = tts_audio_bytes  # Placeholder
            logger.info("Both audio tracks generated. Proper mixing requires FFmpeg integration.")

        # Use the appropriate audio track
        audio_bytes = None
        if audio_type == "background_music":
            audio_bytes = background_music_bytes
        elif audio_type == "text_to_speech":
            audio_bytes = tts_audio_bytes
        elif audio_type == "both":
            audio_bytes = combined_audio_bytes or tts_audio_bytes

        if not audio_bytes:
            logger.error("No audio generated")
            await send_webhook(project_id, f"video_audio_{scene_id or 'full'}", "failed")
            return

        # Combine video and audio using FFmpeg
        logger.info("Combining video and audio using FFmpeg...")
        output_key = None
        if scene_id:
            output_key = generate_s3_key(project_id, "video_with_audio", scene_id)
        else:
            output_key = f"projects/{project_id}/final_video_with_audio.mp4"

        video_with_audio_s3_url = await combine_video_and_audio(
            video_s3_url=video_s3_url,
            audio_bytes=audio_bytes,
            project_id=project_id,
            output_key=output_key
        )

        if not video_with_audio_s3_url:
            logger.error("Failed to combine video and audio")
            await send_webhook(project_id, f"video_audio_{scene_id or 'full'}", "failed")
            return

        logger.info(f"Video with audio uploaded to S3: {video_with_audio_s3_url}")

        # Get presigned URL for webhook
        presigned_url = get_presigned_url_from_s3_url(video_with_audio_s3_url)

        # Determine webhook task type based on audio type
        task_type_suffix = ""
        if audio_type == "background_music":
            task_type_suffix = "_bgm"
        elif audio_type == "text_to_speech":
            task_type_suffix = "_tts"
        else:
            task_type_suffix = "_both"

        # Send webhook notification with presigned URL
        await send_webhook(
            project_id,
            f"video_audio_{scene_id or 'full'}{task_type_suffix}",
            "done",
            presigned_url=presigned_url
        )
        logger.info(f"Audio added to video for {'scene ' + scene_id if scene_id else 'full project'}")

    except Exception as e:
        logger.error(f"Error adding audio to video: {str(e)}")
        await send_webhook(project_id, f"video_audio_{scene_id or 'full'}", "failed")


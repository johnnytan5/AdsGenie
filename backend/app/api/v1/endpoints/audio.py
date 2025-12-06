"""
Audio generation endpoints.
"""
from fastapi import APIRouter, HTTPException, status, BackgroundTasks

from app.schemas.audio import (
    AudioGenerationRequest,
    AudioGenerationResponse,
    VideoAudioRequest,
    VideoAudioResponse,
    BGMGenerationRequest,
    BGMGenerationResponse,
    AddAudioToVideoRequest,
    TTSGenerationRequest,
    TTSGenerationResponse,
)
from app.crud import project as crud_project
from app.tasks.audio import (
    generate_audio_task,
    add_audio_to_video_task,
    generate_bgm_only_task,
    add_bgm_to_video_task,
    generate_tts_only_task,
    add_tts_to_video_task,
)

router = APIRouter()


@router.post("/{project_id}/scenes/{scene_id}/generate-audio", response_model=AudioGenerationResponse)
async def generate_audio(
    project_id: str,
    scene_id: str,
    request: AudioGenerationRequest,
    background_tasks: BackgroundTasks,
):
    """Generate audio (background music, TTS, or both) for a scene."""
    project = crud_project.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    scenes = project.get("scenes", [])
    scene = next((s for s in scenes if s["scene_id"] == scene_id), None)
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found",
        )

    # Validate TTS text if required
    if request.audio_type in ["text_to_speech", "both"]:
        if not request.tts_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tts_text is required when audio_type is 'text_to_speech' or 'both'",
            )

    # Add background task
    background_tasks.add_task(
        generate_audio_task,
        project_id=project_id,
        scene_id=scene_id,
        audio_type=request.audio_type,
        video_description=request.video_description,
        duration=request.duration,
        tts_text=request.tts_text,
        voice_id=request.voice_id,
    )

    return AudioGenerationResponse(
        scene_id=scene_id,
        project_id=project_id,
        audio_type=request.audio_type,
        status="processing",
    )


@router.post("/{project_id}/scenes/{scene_id}/add-audio-to-video", response_model=VideoAudioResponse)
async def add_audio_to_video(
    project_id: str,
    scene_id: str,
    request: VideoAudioRequest,
    background_tasks: BackgroundTasks,
):
    """Add audio (background music, TTS, or both) to a scene video."""
    project = crud_project.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    scenes = project.get("scenes", [])
    scene = next((s for s in scenes if s["scene_id"] == scene_id), None)
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found",
        )

    if not scene.get("generated_video_s3_url"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scene must have a generated video before adding audio",
        )

    # Validate TTS text if required
    if request.audio_type in ["text_to_speech", "both"]:
        if not request.tts_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tts_text is required when audio_type is 'text_to_speech' or 'both'",
            )

    # Add background task
    background_tasks.add_task(
        add_audio_to_video_task,
        project_id=project_id,
        scene_id=scene_id,
        video_s3_url=scene["generated_video_s3_url"],
        audio_type=request.audio_type,
        video_description=request.video_description,
        duration=scene.get("duration", 5),
        tts_text=request.tts_text,
        voice_id=request.voice_id,
    )

    return VideoAudioResponse(
        scene_id=scene_id,
        project_id=project_id,
        status="processing",
    )


@router.post("/{project_id}/add-audio-to-video", response_model=VideoAudioResponse)
async def add_audio_to_full_video(
    project_id: str,
    request: VideoAudioRequest,
    background_tasks: BackgroundTasks,
):
    """Add audio (background music, TTS, or both) to the full project video."""
    project = crud_project.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not project.get("final_video_s3_url"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project must have a final video before adding audio",
        )

    # Validate TTS text if required
    if request.audio_type in ["text_to_speech", "both"]:
        if not request.tts_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tts_text is required when audio_type is 'text_to_speech' or 'both'",
            )

    # Use provided duration or calculate from scenes
    if request.duration:
        total_duration = request.duration
    else:
        scenes = project.get("scenes", [])
        total_duration = sum(scene.get("duration", 5) for scene in scenes)

    # Add background task
    background_tasks.add_task(
        add_audio_to_video_task,
        project_id=project_id,
        scene_id=None,  # None indicates full project video
        video_s3_url=project["final_video_s3_url"],
        audio_type=request.audio_type,
        video_description=request.video_description,
        duration=total_duration,
        tts_text=request.tts_text,
        voice_id=request.voice_id,
        music_type=request.music_type,
        mood=request.mood,
        tempo=request.tempo,
    )

    return VideoAudioResponse(
        project_id=project_id,
        status="processing",
    )


@router.post("/{project_id}/generate-tts", response_model=TTSGenerationResponse)
async def generate_tts_only(
    project_id: str,
    request: TTSGenerationRequest,
    background_tasks: BackgroundTasks,
):
    """Generate TTS audio only (without combining with video)."""
    project = crud_project.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not project.get("final_video_s3_url"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project must have a final video before generating TTS",
        )

    # Add background task
    background_tasks.add_task(
        generate_tts_only_task,
        project_id=project_id,
        tts_text=request.tts_text,
        voice_id=request.voice_id,
    )

    return TTSGenerationResponse(
        project_id=project_id,
        status="processing",
    )


@router.post("/{project_id}/add-tts-to-video", response_model=VideoAudioResponse)
async def add_tts_to_video(
    project_id: str,
    request: AddAudioToVideoRequest,
    background_tasks: BackgroundTasks,
):
    """Add generated TTS audio to video with overlay or overwrite mode."""
    project = crud_project.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not project.get("final_video_s3_url"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project must have a final video before adding TTS",
        )

    # Add background task
    background_tasks.add_task(
        add_tts_to_video_task,
        project_id=project_id,
        audio_s3_url=request.audio_s3_url,
        audio_mode=request.audio_mode,
    )

    return VideoAudioResponse(
        project_id=project_id,
        status="processing",
    )


@router.post("/{project_id}/generate-bgm", response_model=BGMGenerationResponse)
async def generate_bgm_only(
    project_id: str,
    request: BGMGenerationRequest,
    background_tasks: BackgroundTasks,
):
    """Generate BGM audio only (without combining with video)."""
    project = crud_project.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not project.get("final_video_s3_url"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project must have a final video before generating BGM",
        )

    # Add background task
    background_tasks.add_task(
        generate_bgm_only_task,
        project_id=project_id,
        video_description=request.video_description,
        duration=request.duration,
        music_type=request.music_type,
        mood=request.mood,
        tempo=request.tempo,
    )

    return BGMGenerationResponse(
        project_id=project_id,
        status="processing",
    )


@router.post("/{project_id}/add-bgm-to-video", response_model=VideoAudioResponse)
async def add_bgm_to_video(
    project_id: str,
    request: AddAudioToVideoRequest,
    background_tasks: BackgroundTasks,
):
    """Add generated BGM audio to video with overlay or overwrite mode."""
    project = crud_project.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if not project.get("final_video_s3_url"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project must have a final video before adding BGM",
        )

    # Add background task
    background_tasks.add_task(
        add_bgm_to_video_task,
        project_id=project_id,
        audio_s3_url=request.audio_s3_url,
        audio_mode=request.audio_mode,
    )

    return VideoAudioResponse(
        project_id=project_id,
        status="processing",
    )


"""
Image and video generation endpoints.
"""
from fastapi import APIRouter, HTTPException, status, BackgroundTasks

from app.schemas.generation import (
    ImageGenerationRequest,
    ImageGenerationResponse,
    VideoGenerationRequest,
    VideoGenerationResponse,
    FullVideoGenerationRequest,
    FullVideoGenerationResponse,
)
from app.crud import project as crud_project
from app.core.s3 import delete_file_from_s3, generate_s3_key
from app.tasks.generation import (
    generate_scene_image_task,
    generate_scene_video_task,
    generate_full_video_task,
)

router = APIRouter()


@router.post("/{project_id}/scenes/{scene_id}/generate-image", response_model=ImageGenerationResponse)
async def generate_scene_image(
    project_id: str,
    scene_id: str,
    request: ImageGenerationRequest,
    background_tasks: BackgroundTasks,
):
    """Generate image for a scene."""
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

    # Add background task
    background_tasks.add_task(
        generate_scene_image_task,
        project_id=project_id,
        scene_id=scene_id,
        description=scene["description"],
        sketch_s3_url=scene.get("sketch_s3_url"),
        use_global_character=request.use_global_character,
        use_global_setting=request.use_global_setting,
    )

    return ImageGenerationResponse(
        scene_id=scene_id,
        generated_image_s3_url=scene.get("generated_image_s3_url") or "",
        status="processing",
    )


@router.post("/{project_id}/scenes/{scene_id}/generate-video", response_model=VideoGenerationResponse)
async def generate_scene_video(
    project_id: str,
    scene_id: str,
    request: VideoGenerationRequest,
    background_tasks: BackgroundTasks,
):
    """Generate video for a scene."""
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

    if not scene.get("generated_image_s3_url"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scene must have a generated image before generating video",
        )

    # Add background task
    background_tasks.add_task(
        generate_scene_video_task,
        project_id=project_id,
        scene_id=scene_id,
        image_s3_url=scene["generated_image_s3_url"],
        aspect_ratio=request.aspect_ratio,
        voiceover_text=request.voiceover_text,
        duration=scene.get("duration", 5),
    )

    return VideoGenerationResponse(
        scene_id=scene_id,
        generated_video_s3_url=scene.get("generated_video_s3_url") or "",
        status="processing",
    )


@router.delete("/{project_id}/scenes/{scene_id}/generated-image", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scene_generated_image(project_id: str, scene_id: str):
    """Delete scene generated image."""
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

    if scene.get("generated_image_s3_url"):
        image_key = generate_s3_key(project_id, "generated_image", scene_id)
        delete_file_from_s3(image_key)

    crud_project.delete_scene_generated_image(project_id, scene_id)
    return None


@router.delete("/{project_id}/scenes/{scene_id}/generated-video", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scene_generated_video(project_id: str, scene_id: str):
    """Delete scene generated video."""
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

    if scene.get("generated_video_s3_url"):
        video_key = generate_s3_key(project_id, "generated_video", scene_id)
        delete_file_from_s3(video_key)

    crud_project.delete_scene_generated_video(project_id, scene_id)
    return None


@router.post("/{project_id}/generate-video", response_model=FullVideoGenerationResponse)
async def generate_full_video(
    project_id: str,
    request: FullVideoGenerationRequest,
    background_tasks: BackgroundTasks,
):
    """Generate full project video."""
    project = crud_project.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    scenes = project.get("scenes", [])
    if not scenes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project must have at least one scene",
        )

    # Add background task
    background_tasks.add_task(
        generate_full_video_task,
        project_id=project_id,
        aspect_ratio=request.aspect_ratio,
    )

    return FullVideoGenerationResponse(
        project_id=project_id,
        final_video_s3_url=project.get("final_video_s3_url") or "",
        status="processing",
    )

"""
Scene management endpoints.
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from typing import Optional

from app.schemas.scene import SceneCreate, SceneResponse, SceneUpdate, SceneReorderRequest
from app.crud import project as crud_project
from app.core.s3 import upload_file_to_s3, delete_file_from_s3, generate_s3_key

router = APIRouter()


@router.post("/{project_id}/scenes", response_model=SceneResponse, status_code=status.HTTP_201_CREATED)
async def add_scene(
    project_id: str,
    description: str,
    duration: int,
    sketch_file: Optional[UploadFile] = File(None),
):
    """Add a scene to a project."""
    project = crud_project.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    scene_data = SceneCreate(description=description, duration=duration)

    # Create scene first to get scene_id
    updated_project = crud_project.add_scene(project_id, scene_data, sketch_s3_url=None)
    if not updated_project:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create scene",
        )

    # Find the newly created scene
    scenes = updated_project.get("scenes", [])
    new_scene = scenes[-1] if scenes else None

    if not new_scene:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve created scene",
        )

    # Upload sketch if provided (now we have scene_id)
    if sketch_file:
        scene_id = new_scene["scene_id"]
        content = await sketch_file.read()
        s3_key = generate_s3_key(project_id, "sketch", scene_id)
        sketch_s3_url = upload_file_to_s3(content, s3_key, content_type=sketch_file.content_type)
        
        # Update scene with sketch URL
        scene_update = SceneUpdate()
        crud_project.update_scene(project_id, scene_id, scene_update, sketch_s3_url=sketch_s3_url)
        updated_project = crud_project.get_project(project_id)
        scenes = updated_project.get("scenes", [])
        new_scene = next((s for s in scenes if s["scene_id"] == scene_id), None)

    return new_scene


@router.put("/{project_id}/scenes/{scene_id}", response_model=SceneResponse)
async def update_scene(
    project_id: str,
    scene_id: str,
    description: Optional[str] = None,
    duration: Optional[int] = None,
    sketch_file: Optional[UploadFile] = File(None),
):
    """Update a scene."""
    project = crud_project.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check if scene exists
    scenes = project.get("scenes", [])
    scene = next((s for s in scenes if s["scene_id"] == scene_id), None)
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found",
        )

    scene_data = SceneUpdate(description=description, duration=duration)

    # Upload sketch if provided
    sketch_s3_url = None
    if sketch_file:
        content = await sketch_file.read()
        s3_key = generate_s3_key(project_id, "sketch", scene_id)
        sketch_s3_url = upload_file_to_s3(content, s3_key, content_type=sketch_file.content_type)

    updated_project = crud_project.update_scene(project_id, scene_id, scene_data, sketch_s3_url=sketch_s3_url)
    if not updated_project:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update scene",
        )

    # Find updated scene
    scenes = updated_project.get("scenes", [])
    updated_scene = next((s for s in scenes if s["scene_id"] == scene_id), None)

    if not updated_scene:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve updated scene",
        )

    return updated_scene


@router.delete("/{project_id}/scenes/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scene(project_id: str, scene_id: str):
    """Delete a scene and its S3 assets."""
    project = crud_project.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check if scene exists
    scenes = project.get("scenes", [])
    scene = next((s for s in scenes if s["scene_id"] == scene_id), None)
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found",
        )

    # Delete S3 files
    if scene.get("sketch_s3_url"):
        sketch_key = generate_s3_key(project_id, "sketch", scene_id)
        delete_file_from_s3(sketch_key)

    if scene.get("generated_image_s3_url"):
        image_key = generate_s3_key(project_id, "generated_image", scene_id)
        delete_file_from_s3(image_key)

    if scene.get("generated_video_s3_url"):
        video_key = generate_s3_key(project_id, "generated_video", scene_id)
        delete_file_from_s3(video_key)

    # Delete from DynamoDB
    crud_project.delete_scene(project_id, scene_id)
    return None


@router.put("/{project_id}/scenes/reorder", status_code=status.HTTP_200_OK)
async def reorder_scenes(project_id: str, request: SceneReorderRequest):
    """Reorder scenes."""
    project = crud_project.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Convert Pydantic models to dicts
    scene_order = [{"scene_id": item.scene_id, "order": item.order} for item in request.scene_order]

    updated_project = crud_project.reorder_scenes(project_id, scene_order)
    if not updated_project:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reorder scenes",
        )

    return {"success": True}

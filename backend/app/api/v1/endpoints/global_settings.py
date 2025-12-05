"""
Global settings (character and setting) endpoints.
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from typing import Optional

from app.schemas.global_settings import GlobalUpdateRequest, GlobalUpdateResponse
from app.crud import project as crud_project
from app.core.s3 import upload_file_to_s3, delete_file_from_s3, generate_s3_key
from app.services.ai import generate_image_nanobanana
from app.tasks.generation import generate_scene_image_task
import httpx

router = APIRouter()


@router.put("/{project_id}/global", response_model=GlobalUpdateResponse)
async def update_global_settings(
    project_id: str,
    request: GlobalUpdateRequest,
    character_sketch: Optional[UploadFile] = File(None),
    setting_sketch: Optional[UploadFile] = File(None),
):
    """Update global character and/or setting."""
    project = crud_project.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Handle character sketch upload
    character_sketch_s3_url = None
    if character_sketch:
        content = await character_sketch.read()
        s3_key = generate_s3_key(project_id, "character_sketch")
        character_sketch_s3_url = upload_file_to_s3(content, s3_key, content_type=character_sketch.content_type)
        crud_project.update_global_character_s3_urls(project_id, sketch_s3_url=character_sketch_s3_url)

    # Handle setting sketch upload
    setting_sketch_s3_url = None
    if setting_sketch:
        content = await setting_sketch.read()
        s3_key = generate_s3_key(project_id, "setting_sketch")
        setting_sketch_s3_url = upload_file_to_s3(content, s3_key, content_type=setting_sketch.content_type)
        crud_project.update_global_setting_s3_urls(project_id, sketch_s3_url=setting_sketch_s3_url)

    # Update descriptions
    updated_project = crud_project.update_global_settings(
        project_id,
        character=request.character,
        setting=request.setting,
    )

    if not updated_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Generate images if sketches were uploaded
    if character_sketch_s3_url:
        # Background task to generate character image
        global_character = updated_project.get("global_character") or {}
        description = global_character.get("description") or "character"
        # This would trigger background generation
        # For now, we'll do it synchronously (should be backgrounded)
        pass

    if setting_sketch_s3_url:
        # Background task to generate setting image
        global_setting = updated_project.get("global_setting") or {}
        description = global_setting.get("description") or "setting"
        # This would trigger background generation
        pass

    return GlobalUpdateResponse(
        global_character=updated_project.get("global_character"),
        global_setting=updated_project.get("global_setting"),
    )


@router.delete("/{project_id}/global/character", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_character(project_id: str):
    """Delete global character sketch and image."""
    project = crud_project.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    global_character = project.get("global_character")
    if global_character:
        # Delete S3 files
        if global_character.get("sketch_s3_url"):
            # Extract S3 key from URL
            sketch_key = generate_s3_key(project_id, "character_sketch")
            delete_file_from_s3(sketch_key)

        if global_character.get("generated_image_s3_url"):
            image_key = generate_s3_key(project_id, "character_image")
            delete_file_from_s3(image_key)

    # Update DynamoDB
    crud_project.delete_global_character(project_id)
    return None


@router.delete("/{project_id}/global/setting", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_setting(project_id: str):
    """Delete global setting sketch and image."""
    project = crud_project.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    global_setting = project.get("global_setting")
    if global_setting:
        # Delete S3 files
        if global_setting.get("sketch_s3_url"):
            sketch_key = generate_s3_key(project_id, "setting_sketch")
            delete_file_from_s3(sketch_key)

        if global_setting.get("generated_image_s3_url"):
            image_key = generate_s3_key(project_id, "setting_image")
            delete_file_from_s3(image_key)

    # Update DynamoDB
    crud_project.delete_global_setting(project_id)
    return None

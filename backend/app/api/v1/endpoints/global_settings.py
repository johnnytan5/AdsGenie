"""
Global settings (character and setting) endpoints.
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File, BackgroundTasks, Form
from typing import Optional
import json

from app.schemas.global_settings import (
    GlobalUpdateRequest,
    GlobalUpdateResponse,
    GlobalCharacterUpdate,
    GlobalSettingUpdate,
    GlobalCharacter,
    GlobalSetting,
)
from app.crud import project as crud_project
from app.core.s3 import upload_file_to_s3, delete_file_from_s3, generate_s3_key
from app.tasks.generation import (
    generate_global_character_image_task,
    generate_global_setting_image_task,
)

router = APIRouter()


@router.put("/{project_id}/global", response_model=GlobalUpdateResponse)
async def update_global_settings(
    project_id: str,
    background_tasks: BackgroundTasks,
    character: Optional[str] = Form(None),
    setting: Optional[str] = Form(None),
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

    # Parse JSON form fields (handle empty strings and None)
    character_update = None
    if character and character.strip() and character != "null":
        try:
            character_data = json.loads(character)
            if character_data:  # Only create update if data is not empty
                character_update = GlobalCharacterUpdate(**character_data)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            # Log error but don't fail - just skip character update
            print(f"Error parsing character JSON: {e}, raw value: {character[:100]}")

    setting_update = None
    if setting and setting.strip() and setting != "null":
        try:
            setting_data = json.loads(setting)
            if setting_data:  # Only create update if data is not empty
                setting_update = GlobalSettingUpdate(**setting_data)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            # Log error but don't fail - just skip setting update
            print(f"Error parsing setting JSON: {e}, raw value: {setting[:100]}")

    # Handle character sketch upload
    character_sketch_s3_url = None
    if character_sketch and character_sketch.filename:
        try:
            content = await character_sketch.read()
            if content:  # Only upload if content is not empty
                s3_key = generate_s3_key(project_id, "character_sketch")
                character_sketch_s3_url = upload_file_to_s3(content, s3_key, content_type=character_sketch.content_type or "image/png")
                crud_project.update_global_character_s3_urls(project_id, sketch_s3_url=character_sketch_s3_url)
        except Exception as e:
            print(f"Error uploading character sketch: {e}")

    # Handle setting sketch upload
    setting_sketch_s3_url = None
    if setting_sketch and setting_sketch.filename:
        try:
            content = await setting_sketch.read()
            if content:  # Only upload if content is not empty
                s3_key = generate_s3_key(project_id, "setting_sketch")
                setting_sketch_s3_url = upload_file_to_s3(content, s3_key, content_type=setting_sketch.content_type or "image/png")
                crud_project.update_global_setting_s3_urls(project_id, sketch_s3_url=setting_sketch_s3_url)
        except Exception as e:
            print(f"Error uploading setting sketch: {e}")

    # Update descriptions
    updated_project = crud_project.update_global_settings(
        project_id,
        character=character_update,
        setting=setting_update,
    )

    if not updated_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Generate images if character update was provided OR if character sketch was uploaded
    # This allows generation to be triggered by either updating description or uploading sketch
    global_character = updated_project.get("global_character") or {}
    character_description = global_character.get("description")
    character_has_sketch = character_sketch_s3_url or global_character.get("sketch_s3_url")
    
    # Trigger generation if:
    # 1. Character update was provided (description changed), OR
    # 2. Character sketch was uploaded, OR  
    # 3. We have a description (even if no sketch - text-only generation)
    # Note: When user clicks "Generate Character Image", character_update may be None
    # if description hasn't changed, but we still want to generate if description exists
    should_generate_character = (
        character_update is not None or  # Description was updated
        character_sketch_s3_url or  # Sketch was uploaded
        (character_description and character_description.strip())  # Description exists (text-only generation)
    )
    
    if should_generate_character:
        description = character_description or "Generate a high-quality character image"
        sketch_url = character_sketch_s3_url or global_character.get("sketch_s3_url") or ""
        
        # Only trigger if we have at least a description
        if description and description.strip():
            print(f"Triggering character image generation for project {project_id} with description: {description[:100]}")
            # Add background task to generate character image using Google GenAI
            background_tasks.add_task(
                generate_global_character_image_task,
                project_id=project_id,
                description=description,
                sketch_s3_url=sketch_url,
            )

    # Generate images if setting update was provided OR if setting sketch was uploaded
    global_setting = updated_project.get("global_setting") or {}
    setting_description = global_setting.get("description")
    setting_has_sketch = setting_sketch_s3_url or global_setting.get("sketch_s3_url")
    
    # Trigger generation if:
    # 1. Setting update was provided (description changed), OR
    # 2. Setting sketch was uploaded, OR
    # 3. We have a description (even if no sketch - text-only generation)
    should_generate_setting = (
        setting_update is not None or  # Description was updated
        setting_sketch_s3_url or  # Sketch was uploaded
        (setting_description and setting_description.strip())  # Description exists (text-only generation)
    )
    
    if should_generate_setting:
        description = setting_description or "Generate a high-quality setting image"
        sketch_url = setting_sketch_s3_url or global_setting.get("sketch_s3_url") or ""
        
        # Only trigger if we have at least a description
        if description and description.strip():
            print(f"Triggering setting image generation for project {project_id} with description: {description[:100]}")
            # Add background task to generate setting image using Google GenAI
            background_tasks.add_task(
                generate_global_setting_image_task,
                project_id=project_id,
                description=description,
                sketch_s3_url=sketch_url,
            )

    # Convert None values to None, or create schema objects from dicts
    global_character = updated_project.get("global_character")
    global_setting = updated_project.get("global_setting")
    
    return GlobalUpdateResponse(
        global_character=GlobalCharacter(**global_character) if global_character else None,
        global_setting=GlobalSetting(**global_setting) if global_setting else None,
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

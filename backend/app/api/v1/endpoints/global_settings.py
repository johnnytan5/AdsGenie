"""
Global settings (character and setting) endpoints.
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File, BackgroundTasks, Form
from typing import Optional
import json

from app.schemas.global_settings import GlobalUpdateRequest, GlobalUpdateResponse, GlobalCharacterUpdate, GlobalSettingUpdate
from app.crud import project as crud_project
from app.core.s3 import upload_file_to_s3, delete_file_from_s3, generate_s3_key, get_presigned_url_from_s3_url
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
    # If character/setting field is provided (even if empty), it means generate button was pressed
    character_update = None
    print(f"[DEBUG] Received character form field: {character}")
    if character and character.strip() and character != "null" and character != "undefined":
        try:
            character_data = json.loads(character)
            # Always create update object if JSON is provided (even if fields are empty)
            # This indicates the generate button was pressed
            character_update = GlobalCharacterUpdate(**character_data)
            print(f"[DEBUG] Parsed character_update: name='{character_update.name}', description='{character_update.description}'")
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            # Log error but don't fail - just skip character update
            print(f"Error parsing character JSON: {e}, raw value: {character[:100]}")

    setting_update = None
    print(f"[DEBUG] Received setting form field: {setting}")
    if setting and setting.strip() and setting != "null" and setting != "undefined":
        try:
            setting_data = json.loads(setting)
            # Always create update object if JSON is provided (even if fields are empty)
            # This indicates the generate button was pressed
            setting_update = GlobalSettingUpdate(**setting_data)
            print(f"[DEBUG] Parsed setting_update: name='{setting_update.name}', description='{setting_update.description}'")
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            # Log error but don't fail - just skip setting update
            print(f"Error parsing setting JSON: {e}, raw value: {setting[:100]}")
    
    print(f"[DEBUG] Final character_update: {character_update}")
    print(f"[DEBUG] Final setting_update: {setting_update}")

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

    # Generate images if sketches were uploaded OR if character_update was provided (button was pressed)
    # If character_update is provided, it means the generate button was pressed - always trigger generation
    should_generate_character = (
        character_sketch_s3_url is not None or  # Sketch was uploaded
        character_update is not None  # Generate button was pressed (even if description is empty)
    )
    
    if should_generate_character:
        global_character = updated_project.get("global_character") or {}
        # Use description from update, or from existing character, or default
        description = (
            (character_update and character_update.description and character_update.description.strip()) or
            global_character.get("description") or 
            "Generate a high-quality character image"
        )
        sketch_url = character_sketch_s3_url or global_character.get("sketch_s3_url") or ""
        
        print(f"[DEBUG] Triggering character image generation for project {project_id}")
        print(f"[DEBUG] Description: {description[:100]}")
        print(f"[DEBUG] Sketch URL: {sketch_url or 'None'}")
        
        # Add background task to generate character image using Google GenAI
        background_tasks.add_task(
            generate_global_character_image_task,
            project_id=project_id,
            description=description,
            sketch_s3_url=sketch_url,
        )

    # Generate images if sketches were uploaded OR if setting_update was provided (button was pressed)
    # If setting_update is provided, it means the generate button was pressed - always trigger generation
    should_generate_setting = (
        setting_sketch_s3_url is not None or  # Sketch was uploaded
        setting_update is not None  # Generate button was pressed (even if description is empty)
    )
    
    if should_generate_setting:
        global_setting = updated_project.get("global_setting") or {}
        # Use description from update, or from existing setting, or default
        description = (
            (setting_update and setting_update.description and setting_update.description.strip()) or
            global_setting.get("description") or 
            "Generate a high-quality setting image"
        )
        sketch_url = setting_sketch_s3_url or global_setting.get("sketch_s3_url") or ""
        
        print(f"[DEBUG] Triggering setting image generation for project {project_id}")
        print(f"[DEBUG] Description: {description[:100]}")
        print(f"[DEBUG] Sketch URL: {sketch_url or 'None'}")
        
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
    
    from app.schemas.global_settings import GlobalCharacter, GlobalSetting
    
    # Convert S3 URLs to presigned URLs for frontend access
    if global_character:
        global_character = global_character.copy()
        if global_character.get("sketch_s3_url"):
            global_character["sketch_s3_url"] = get_presigned_url_from_s3_url(global_character["sketch_s3_url"])
        if global_character.get("generated_image_s3_url"):
            global_character["generated_image_s3_url"] = get_presigned_url_from_s3_url(global_character["generated_image_s3_url"])
    
    if global_setting:
        global_setting = global_setting.copy()
        if global_setting.get("sketch_s3_url"):
            global_setting["sketch_s3_url"] = get_presigned_url_from_s3_url(global_setting["sketch_s3_url"])
        if global_setting.get("generated_image_s3_url"):
            global_setting["generated_image_s3_url"] = get_presigned_url_from_s3_url(global_setting["generated_image_s3_url"])
    
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

"""
Project management endpoints.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from app.crud import project as crud_project
from app.core.s3 import delete_prefix_from_s3, generate_s3_key, get_presigned_url_from_s3_url

router = APIRouter()


def convert_project_s3_urls_to_presigned(project: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert all S3 URLs in a project to presigned URLs for frontend access.
    
    Args:
        project: Project dictionary from DynamoDB
        
    Returns:
        Project dictionary with presigned URLs
    """
    # Create a copy to avoid modifying the original
    project = project.copy()
    
    # Convert global character image URLs
    if project.get("global_character"):
        global_character = project["global_character"].copy()
        if global_character.get("sketch_s3_url"):
            global_character["sketch_s3_url"] = get_presigned_url_from_s3_url(global_character["sketch_s3_url"])
        if global_character.get("generated_image_s3_url"):
            global_character["generated_image_s3_url"] = get_presigned_url_from_s3_url(global_character["generated_image_s3_url"])
        project["global_character"] = global_character
    
    # Convert global setting image URLs
    if project.get("global_setting"):
        global_setting = project["global_setting"].copy()
        if global_setting.get("sketch_s3_url"):
            global_setting["sketch_s3_url"] = get_presigned_url_from_s3_url(global_setting["sketch_s3_url"])
        if global_setting.get("generated_image_s3_url"):
            global_setting["generated_image_s3_url"] = get_presigned_url_from_s3_url(global_setting["generated_image_s3_url"])
        project["global_setting"] = global_setting
    
    # Convert scene image/video URLs
    if project.get("scenes"):
        scenes = []
        for scene in project["scenes"]:
            scene = scene.copy()
            if scene.get("sketch_s3_url"):
                scene["sketch_s3_url"] = get_presigned_url_from_s3_url(scene["sketch_s3_url"])
            if scene.get("generated_image_s3_url"):
                scene["generated_image_s3_url"] = get_presigned_url_from_s3_url(scene["generated_image_s3_url"])
            if scene.get("generated_video_s3_url"):
                scene["generated_video_s3_url"] = get_presigned_url_from_s3_url(scene["generated_video_s3_url"])
            scenes.append(scene)
        project["scenes"] = scenes
    
    # Convert final video URL
    if project.get("final_video_s3_url"):
        project["final_video_s3_url"] = get_presigned_url_from_s3_url(project["final_video_s3_url"])
    
    return project


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project_data: ProjectCreate):
    """Create a new project."""
    project = crud_project.create_project(project_data)
    return project


@router.get("", response_model=List[ProjectListResponse])
async def list_projects():
    """List all projects."""
    projects = crud_project.list_projects()
    # Convert thumbnail S3 URLs to presigned URLs for frontend access
    # Note: list_projects returns simplified structure, only has thumbnail_s3_url
    for project in projects:
        if project.get("thumbnail_s3_url"):
            project["thumbnail_s3_url"] = get_presigned_url_from_s3_url(project["thumbnail_s3_url"])
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get project details."""
    project = crud_project.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    # Convert S3 URLs to presigned URLs for frontend access
    project = convert_project_s3_urls_to_presigned(project)
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, project_data: ProjectUpdate):
    """Update project details."""
    project = crud_project.update_project(project_id, project_data)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    # Convert S3 URLs to presigned URLs for frontend access
    project = convert_project_s3_urls_to_presigned(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str):
    """Delete a project and all its S3 assets."""
    project = crud_project.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Delete all S3 assets for this project
    prefix = f"projects/{project_id}/"
    delete_prefix_from_s3(prefix)

    # Delete project from DynamoDB
    crud_project.delete_project(project_id)
    return None

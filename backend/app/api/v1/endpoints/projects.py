"""
Project management endpoints.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List

from app.schemas.project import ProjectCreate, ProjectResponse, ProjectListResponse
from app.crud import project as crud_project
from app.core.s3 import delete_prefix_from_s3, generate_s3_key

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project_data: ProjectCreate):
    """Create a new project."""
    project = crud_project.create_project(project_data)
    return project


@router.get("", response_model=List[ProjectListResponse])
async def list_projects():
    """List all projects."""
    projects = crud_project.list_projects()
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

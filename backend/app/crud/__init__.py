"""
CRUD operations for database models.
"""
from app.crud.project import (
    create_project,
    get_project,
    list_projects,
    update_project,
    delete_project,
    update_global_settings,
    delete_global_character,
    delete_global_setting,
    add_scene,
    update_scene,
    delete_scene,
    reorder_scenes,
    update_scene_status,
    update_scene_generated_image,
    update_scene_generated_video,
    delete_scene_generated_image,
    delete_scene_generated_video,
    update_final_video,
)

__all__ = [
    "create_project",
    "get_project",
    "list_projects",
    "update_project",
    "delete_project",
    "update_global_settings",
    "delete_global_character",
    "delete_global_setting",
    "add_scene",
    "update_scene",
    "delete_scene",
    "reorder_scenes",
    "update_scene_status",
    "update_scene_generated_image",
    "update_scene_generated_video",
    "delete_scene_generated_image",
    "delete_scene_generated_video",
    "update_final_video",
]

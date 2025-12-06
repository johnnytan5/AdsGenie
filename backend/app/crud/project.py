"""
CRUD operations for Projects in DynamoDB.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from botocore.exceptions import ClientError

from app.core.dynamodb import get_projects_table
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.global_settings import GlobalCharacterUpdate, GlobalSettingUpdate
from app.schemas.scene import SceneCreate, SceneUpdate


def create_project(project_data: ProjectCreate) -> Dict[str, Any]:
    """
    Create a new project in DynamoDB.

    Args:
        project_data: Project creation data

    Returns:
        Created project dictionary
    """
    project_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    project = {
        "project_id": project_id,
        "name": project_data.name,
        "aspect_ratio": project_data.aspect_ratio,
        "global_character": None,
        "global_setting": None,
        "scenes": [],
        "final_video_s3_url": None,
        "created_at": now,
        "updated_at": now,
    }

    table = get_projects_table()
    table.put_item(Item=project)

    return project


def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a project by ID.

    Args:
        project_id: Project ID

    Returns:
        Project dictionary or None if not found
    """
    table = get_projects_table()
    try:
        response = table.get_item(Key={"project_id": project_id})
        return response.get("Item")
    except ClientError:
        return None


def list_projects() -> List[Dict[str, Any]]:
    """
    List all projects.

    Returns:
        List of project dictionaries (limited fields)
    """
    table = get_projects_table()
    response = table.scan()

    projects = []
    for item in response.get("Items", []):
        # Get first scene's generated image as thumbnail, or None
        thumbnail_s3_url = None
        scenes = item.get("scenes", [])
        if scenes:
            first_scene = scenes[0]
            thumbnail_s3_url = first_scene.get("generated_image_s3_url")

        projects.append({
            "project_id": item["project_id"],
            "name": item["name"],
            "thumbnail_s3_url": thumbnail_s3_url,
            "updated_at": item["updated_at"],
        })

    # Sort by updated_at descending
    projects.sort(key=lambda x: x["updated_at"], reverse=True)
    return projects


def update_project(project_id: str, project_data: ProjectUpdate) -> Optional[Dict[str, Any]]:
    """
    Update a project.

    Args:
        project_id: Project ID
        project_data: Project update data

    Returns:
        Updated project dictionary or None if not found
    """
    table = get_projects_table()
    update_expression_parts = []
    expression_attribute_values = {}
    expression_attribute_names = {}

    if project_data.name is not None:
        update_expression_parts.append("#name = :name")
        expression_attribute_names["#name"] = "name"
        expression_attribute_values[":name"] = project_data.name

    if project_data.aspect_ratio is not None:
        update_expression_parts.append("#aspect_ratio = :aspect_ratio")
        expression_attribute_names["#aspect_ratio"] = "aspect_ratio"
        expression_attribute_values[":aspect_ratio"] = project_data.aspect_ratio

    if not update_expression_parts:
        return get_project(project_id)

    update_expression_parts.append("updated_at = :updated_at")
    expression_attribute_values[":updated_at"] = datetime.now(timezone.utc).isoformat()

    update_expression = "SET " + ", ".join(update_expression_parts)

    try:
        table.update_item(
            Key={"project_id": project_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names if expression_attribute_names else None,
            ReturnValues="ALL_NEW",
        )
        return get_project(project_id)
    except ClientError:
        return None


def delete_project(project_id: str) -> bool:
    """
    Delete a project.

    Args:
        project_id: Project ID

    Returns:
        True if deleted, False if not found
    """
    table = get_projects_table()
    try:
        table.delete_item(Key={"project_id": project_id})
        return True
    except ClientError:
        return False


def update_global_settings(
    project_id: str,
    character: Optional[GlobalCharacterUpdate],
    setting: Optional[GlobalSettingUpdate],
) -> Optional[Dict[str, Any]]:
    """
    Update global character and/or setting.

    Args:
        project_id: Project ID
        character: Optional character update
        setting: Optional setting update

    Returns:
        Updated project dictionary or None if not found
    """
    project = get_project(project_id)
    if not project:
        return None

    update_expression_parts = []
    expression_attribute_values = {}
    expression_attribute_names = {}

    if character:
        # Check if global_character exists, if not initialize it
        existing_character = project.get("global_character")
        if not existing_character:
            # Initialize global_character as a new object
            char_data = {}
            if character.description is not None:
                char_data["description"] = character.description
            if character.name is not None:
                char_data["name"] = character.name
            if char_data:
                update_expression_parts.append("global_character = :char_init")
                expression_attribute_values[":char_init"] = char_data
        else:
            # Update existing nested fields
            if character.description is not None:
                update_expression_parts.append("global_character.#char_desc = :char_desc")
                expression_attribute_names["#char_desc"] = "description"
                expression_attribute_values[":char_desc"] = character.description
            if character.name is not None:
                update_expression_parts.append("global_character.#char_name = :char_name")
                expression_attribute_names["#char_name"] = "name"
                expression_attribute_values[":char_name"] = character.name

    if setting:
        # Check if global_setting exists, if not initialize it
        existing_setting = project.get("global_setting")
        if not existing_setting:
            # Initialize global_setting as a new object
            set_data = {}
            if setting.description is not None:
                set_data["description"] = setting.description
            if setting.name is not None:
                set_data["name"] = setting.name
            if set_data:
                update_expression_parts.append("global_setting = :set_init")
                expression_attribute_values[":set_init"] = set_data
        else:
            # Update existing nested fields
            if setting.description is not None:
                update_expression_parts.append("global_setting.#set_desc = :set_desc")
                expression_attribute_names["#set_desc"] = "description"
                expression_attribute_values[":set_desc"] = setting.description
            if setting.name is not None:
                update_expression_parts.append("global_setting.#set_name = :set_name")
                expression_attribute_names["#set_name"] = "name"
                expression_attribute_values[":set_name"] = setting.name

    if not update_expression_parts:
        return project

    update_expression_parts.append("updated_at = :updated_at")
    expression_attribute_values[":updated_at"] = datetime.now(timezone.utc).isoformat()

    update_expression = "SET " + ", ".join(update_expression_parts)

    table = get_projects_table()
    try:
        update_params = {
            "Key": {"project_id": project_id},
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expression_attribute_values,
            "ReturnValues": "ALL_NEW",
        }
        
        # Only include ExpressionAttributeNames if it's not empty
        if expression_attribute_names:
            update_params["ExpressionAttributeNames"] = expression_attribute_names
        
        table.update_item(**update_params)
        return get_project(project_id)
    except ClientError as e:
        print(f"Error updating global settings: {e}")
        import traceback
        traceback.print_exc()
        return None


def update_global_character_s3_urls(
    project_id: str,
    sketch_s3_url: Optional[str] = None,
    generated_image_s3_url: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update global character S3 URLs."""
    project = get_project(project_id)
    if not project:
        return None

    table = get_projects_table()
    update_parts = []
    expression_attribute_values = {}

    if sketch_s3_url is not None:
        update_parts.append("global_character.sketch_s3_url = :sketch_url")
        expression_attribute_values[":sketch_url"] = sketch_s3_url

    if generated_image_s3_url is not None:
        update_parts.append("global_character.generated_image_s3_url = :img_url")
        expression_attribute_values[":img_url"] = generated_image_s3_url

    if not update_parts:
        return project

    update_parts.append("updated_at = :updated_at")
    expression_attribute_values[":updated_at"] = datetime.now(timezone.utc).isoformat()

    try:
        table.update_item(
            Key={"project_id": project_id},
            UpdateExpression="SET " + ", ".join(update_parts),
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW",
        )
        return get_project(project_id)
    except ClientError:
        return None


def update_global_setting_s3_urls(
    project_id: str,
    sketch_s3_url: Optional[str] = None,
    generated_image_s3_url: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update global setting S3 URLs."""
    project = get_project(project_id)
    if not project:
        return None

    table = get_projects_table()
    update_parts = []
    expression_attribute_values = {}

    if sketch_s3_url is not None:
        update_parts.append("global_setting.sketch_s3_url = :sketch_url")
        expression_attribute_values[":sketch_url"] = sketch_s3_url

    if generated_image_s3_url is not None:
        update_parts.append("global_setting.generated_image_s3_url = :img_url")
        expression_attribute_values[":img_url"] = generated_image_s3_url

    if not update_parts:
        return project

    update_parts.append("updated_at = :updated_at")
    expression_attribute_values[":updated_at"] = datetime.now(timezone.utc).isoformat()

    try:
        table.update_item(
            Key={"project_id": project_id},
            UpdateExpression="SET " + ", ".join(update_parts),
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW",
        )
        return get_project(project_id)
    except ClientError:
        return None


def delete_global_character(project_id: str) -> Optional[Dict[str, Any]]:
    """Delete global character (set to None)."""
    table = get_projects_table()
    try:
        table.update_item(
            Key={"project_id": project_id},
            UpdateExpression="SET global_character = :null, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":null": None,
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        return get_project(project_id)
    except ClientError:
        return None


def delete_global_setting(project_id: str) -> Optional[Dict[str, Any]]:
    """Delete global setting (set to None)."""
    table = get_projects_table()
    try:
        table.update_item(
            Key={"project_id": project_id},
            UpdateExpression="SET global_setting = :null, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":null": None,
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        return get_project(project_id)
    except ClientError:
        return None


def add_scene(project_id: str, scene_data: SceneCreate, sketch_s3_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Add a scene to a project."""
    project = get_project(project_id)
    if not project:
        return None

    scene_id = str(uuid.uuid4())
    scenes = project.get("scenes", [])
    max_order = max([s.get("order", 0) for s in scenes], default=0)

    new_scene = {
        "scene_id": scene_id,
        "order": max_order + 1,
        "duration": scene_data.duration,
        "description": scene_data.description,
        "image_description": None,  # Initialize as None, can be set later
        "sketch_s3_url": sketch_s3_url,
        "generated_image_s3_url": None,
        "generated_video_s3_url": None,
        "status": "pending",
        "voiceover_enabled": False,
        "voiceover_text": None,
        "voiceover_gender": "male",
        "background_music_enabled": False,
        "use_global_character_for_image": False,
        "use_global_setting_for_image": False,
    }

    scenes.append(new_scene)

    table = get_projects_table()
    try:
        table.update_item(
            Key={"project_id": project_id},
            UpdateExpression="SET scenes = :scenes, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":scenes": scenes,
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        return get_project(project_id)
    except ClientError:
        return None


def update_scene(
    project_id: str,
    scene_id: str,
    scene_data: SceneUpdate,
    sketch_s3_url: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update a scene."""
    project = get_project(project_id)
    if not project:
        return None

    scenes = project.get("scenes", [])
    scene_index = next((i for i, s in enumerate(scenes) if s["scene_id"] == scene_id), None)
    if scene_index is None:
        return None

    scene = scenes[scene_index]
    if scene_data.description is not None:
        scene["description"] = scene_data.description
    if scene_data.duration is not None:
        scene["duration"] = scene_data.duration
    if sketch_s3_url is not None:
        scene["sketch_s3_url"] = sketch_s3_url
        # Reset status to pending if sketch changed
        scene["status"] = "pending"
    # Update image_description field (separate from description)
    if scene_data.image_description is not None:
        scene["image_description"] = scene_data.image_description
    
    # Update image generation settings
    if scene_data.use_global_character_for_image is not None:
        scene["use_global_character_for_image"] = scene_data.use_global_character_for_image
    if scene_data.use_global_setting_for_image is not None:
        scene["use_global_setting_for_image"] = scene_data.use_global_setting_for_image
    
    # Update audio fields
    if scene_data.voiceover_enabled is not None:
        scene["voiceover_enabled"] = scene_data.voiceover_enabled
    if scene_data.voiceover_text is not None:
        scene["voiceover_text"] = scene_data.voiceover_text
    if scene_data.voiceover_gender is not None:
        scene["voiceover_gender"] = scene_data.voiceover_gender
    if scene_data.background_music_enabled is not None:
        scene["background_music_enabled"] = scene_data.background_music_enabled

    table = get_projects_table()
    try:
        table.update_item(
            Key={"project_id": project_id},
            UpdateExpression="SET scenes = :scenes, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":scenes": scenes,
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        return get_project(project_id)
    except ClientError:
        return None


def delete_scene(project_id: str, scene_id: str) -> Optional[Dict[str, Any]]:
    """Delete a scene."""
    project = get_project(project_id)
    if not project:
        return None

    scenes = project.get("scenes", [])
    scenes = [s for s in scenes if s["scene_id"] != scene_id]

    table = get_projects_table()
    try:
        table.update_item(
            Key={"project_id": project_id},
            UpdateExpression="SET scenes = :scenes, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":scenes": scenes,
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        return get_project(project_id)
    except ClientError:
        return None


def reorder_scenes(project_id: str, scene_order: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Reorder scenes."""
    project = get_project(project_id)
    if not project:
        return None

    scenes = project.get("scenes", [])
    scene_dict = {s["scene_id"]: s for s in scenes}

    # Update order for each scene
    for item in scene_order:
        scene_id = item["scene_id"]
        if scene_id in scene_dict:
            scene_dict[scene_id]["order"] = item["order"]

    # Sort scenes by order
    scenes = sorted(scene_dict.values(), key=lambda x: x["order"])

    table = get_projects_table()
    try:
        table.update_item(
            Key={"project_id": project_id},
            UpdateExpression="SET scenes = :scenes, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":scenes": scenes,
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        return get_project(project_id)
    except ClientError:
        return None


def update_scene_status(project_id: str, scene_id: str, status: str) -> Optional[Dict[str, Any]]:
    """Update scene status."""
    project = get_project(project_id)
    if not project:
        return None

    scenes = project.get("scenes", [])
    scene_index = next((i for i, s in enumerate(scenes) if s["scene_id"] == scene_id), None)
    if scene_index is None:
        return None

    scenes[scene_index]["status"] = status

    table = get_projects_table()
    try:
        table.update_item(
            Key={"project_id": project_id},
            UpdateExpression="SET scenes = :scenes, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":scenes": scenes,
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        return get_project(project_id)
    except ClientError:
        return None


def update_scene_generated_image(project_id: str, scene_id: str, generated_image_s3_url: str) -> Optional[Dict[str, Any]]:
    """Update scene generated image URL."""
    project = get_project(project_id)
    if not project:
        return None

    scenes = project.get("scenes", [])
    scene_index = next((i for i, s in enumerate(scenes) if s["scene_id"] == scene_id), None)
    if scene_index is None:
        return None

    scenes[scene_index]["generated_image_s3_url"] = generated_image_s3_url
    scenes[scene_index]["status"] = "done"

    table = get_projects_table()
    try:
        table.update_item(
            Key={"project_id": project_id},
            UpdateExpression="SET scenes = :scenes, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":scenes": scenes,
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        return get_project(project_id)
    except ClientError:
        return None


def update_scene_generated_video(project_id: str, scene_id: str, generated_video_s3_url: str) -> Optional[Dict[str, Any]]:
    """Update scene generated video URL."""
    project = get_project(project_id)
    if not project:
        return None

    scenes = project.get("scenes", [])
    scene_index = next((i for i, s in enumerate(scenes) if s["scene_id"] == scene_id), None)
    if scene_index is None:
        return None

    scenes[scene_index]["generated_video_s3_url"] = generated_video_s3_url
    scenes[scene_index]["status"] = "done"

    table = get_projects_table()
    try:
        table.update_item(
            Key={"project_id": project_id},
            UpdateExpression="SET scenes = :scenes, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":scenes": scenes,
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        return get_project(project_id)
    except ClientError:
        return None


def delete_scene_generated_image(project_id: str, scene_id: str) -> Optional[Dict[str, Any]]:
    """Delete scene generated image."""
    project = get_project(project_id)
    if not project:
        return None

    scenes = project.get("scenes", [])
    scene_index = next((i for i, s in enumerate(scenes) if s["scene_id"] == scene_id), None)
    if scene_index is None:
        return None

    scenes[scene_index]["generated_image_s3_url"] = None
    scenes[scene_index]["status"] = "pending"

    table = get_projects_table()
    try:
        table.update_item(
            Key={"project_id": project_id},
            UpdateExpression="SET scenes = :scenes, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":scenes": scenes,
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        return get_project(project_id)
    except ClientError:
        return None


def delete_scene_generated_video(project_id: str, scene_id: str) -> Optional[Dict[str, Any]]:
    """Delete scene generated video."""
    project = get_project(project_id)
    if not project:
        return None

    scenes = project.get("scenes", [])
    scene_index = next((i for i, s in enumerate(scenes) if s["scene_id"] == scene_id), None)
    if scene_index is None:
        return None

    scenes[scene_index]["generated_video_s3_url"] = None
    scenes[scene_index]["status"] = "pending"

    table = get_projects_table()
    try:
        table.update_item(
            Key={"project_id": project_id},
            UpdateExpression="SET scenes = :scenes, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":scenes": scenes,
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        return get_project(project_id)
    except ClientError:
        return None


def update_final_video(project_id: str, final_video_s3_url: str) -> Optional[Dict[str, Any]]:
    """Update final video URL."""
    table = get_projects_table()
    try:
        table.update_item(
            Key={"project_id": project_id},
            UpdateExpression="SET final_video_s3_url = :url, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":url": final_video_s3_url,
                ":updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        return get_project(project_id)
    except ClientError:
        return None

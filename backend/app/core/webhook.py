"""
Webhook utilities for notifying frontend of task completion.
"""
import httpx
from typing import Optional
from app.core.config import settings


async def send_webhook(
    project_id: str,
    task_type: str,
    status: str = "done",
) -> bool:
    """
    Send webhook notification to frontend when a background task completes.

    Args:
        project_id: Project ID
        task_type: Type of task (e.g., "scene_image_{scene_id}", "global_character", "final_video")
        status: Task status ("done" or "failed")

    Returns:
        True if webhook was sent successfully, False otherwise
    """
    try:
        webhook_url = f"{settings.FRONTEND_URL}/api/webhooks/project-update"
        print(f"[WEBHOOK] Attempting to send webhook to {webhook_url}")
        print(f"[WEBHOOK] Payload: project_id={project_id}, task_type={task_type}, status={status}")
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                webhook_url,
                json={
                    "project_id": project_id,
                    "task_type": task_type,
                    "status": status,
                },
            )
            response.raise_for_status()
            print(f"[WEBHOOK] Webhook sent successfully, status code: {response.status_code}")
            return True
    except httpx.TimeoutException as e:
        print(f"[WEBHOOK] Failed to send webhook for {task_type} (project {project_id}): Timeout - {e}")
        return False
    except httpx.HTTPStatusError as e:
        print(f"[WEBHOOK] Failed to send webhook for {task_type} (project {project_id}): HTTP {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        # Log error but don't fail the task
        import traceback
        print(f"[WEBHOOK] Failed to send webhook for {task_type} (project {project_id}): {type(e).__name__} - {e}")
        print(f"[WEBHOOK] Traceback: {traceback.format_exc()}")
        return False

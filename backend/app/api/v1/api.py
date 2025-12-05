"""
Main API router that includes all endpoint routers.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    health,
    projects,
    global_settings,
    scenes,
    generation,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(global_settings.router, prefix="/projects", tags=["global-settings"])
api_router.include_router(scenes.router, prefix="/projects", tags=["scenes"])
api_router.include_router(generation.router, prefix="/projects", tags=["generation"])

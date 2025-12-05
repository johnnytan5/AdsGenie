"""
Example Pydantic schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ExampleBase(BaseModel):
    """Base schema for Example."""

    name: str
    description: Optional[str] = None


class ExampleCreate(ExampleBase):
    """Schema for creating an Example."""

    pass


class ExampleUpdate(BaseModel):
    """Schema for updating an Example."""

    name: Optional[str] = None
    description: Optional[str] = None


class ExampleResponse(ExampleBase):
    """Schema for Example response."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

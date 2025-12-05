"""
Example endpoints for demonstration.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.example import ExampleResponse, ExampleCreate
from app.models.example import Example
from app.crud import example as crud_example

router = APIRouter()


@router.get("", response_model=list[ExampleResponse])
async def get_examples(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get all examples."""
    examples = crud_example.get_examples(db, skip=skip, limit=limit)
    return examples


@router.post("", response_model=ExampleResponse, status_code=201)
async def create_example(
    example: ExampleCreate,
    db: Session = Depends(get_db),
):
    """Create a new example."""
    return crud_example.create_example(db=db, example=example)


@router.get("/{example_id}", response_model=ExampleResponse)
async def get_example(
    example_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific example by ID."""
    example = crud_example.get_example(db, example_id=example_id)
    if not example:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Example not found")
    return example

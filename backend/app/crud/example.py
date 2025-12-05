"""
CRUD operations for Example model.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.example import Example
from app.schemas.example import ExampleCreate, ExampleUpdate


def get_example(db: Session, example_id: int) -> Optional[Example]:
    """Get a single example by ID."""
    return db.query(Example).filter(Example.id == example_id).first()


def get_examples(db: Session, skip: int = 0, limit: int = 100) -> List[Example]:
    """Get multiple examples with pagination."""
    return db.query(Example).offset(skip).limit(limit).all()


def create_example(db: Session, example: ExampleCreate) -> Example:
    """Create a new example."""
    db_example = Example(**example.model_dump())
    db.add(db_example)
    db.commit()
    db.refresh(db_example)
    return db_example


def update_example(
    db: Session, example_id: int, example: ExampleUpdate
) -> Optional[Example]:
    """Update an existing example."""
    db_example = get_example(db, example_id)
    if not db_example:
        return None

    update_data = example.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_example, field, value)

    db.commit()
    db.refresh(db_example)
    return db_example


def delete_example(db: Session, example_id: int) -> bool:
    """Delete an example."""
    db_example = get_example(db, example_id)
    if not db_example:
        return False

    db.delete(db_example)
    db.commit()
    return True

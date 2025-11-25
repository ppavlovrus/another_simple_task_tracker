"""Task Pydantic schemas."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class TaskCreate(BaseModel):
    """Request model for creating a new task."""

    title: str
    description: Optional[str] = None
    status_id: int
    creator_id: int
    deadline_start: Optional[date] = None
    deadline_end: Optional[date] = None


class TaskUpdate(BaseModel):
    """Request model for updating a task."""

    title: Optional[str] = None
    description: Optional[str] = None
    status_id: Optional[int] = None
    deadline_start: Optional[date] = None
    deadline_end: Optional[date] = None


class TaskResponse(BaseModel):
    """Response model for task data."""

    id: int
    title: str
    description: Optional[str]
    status_id: int
    creator_id: int
    deadline_start: Optional[date]
    deadline_end: Optional[date]
    created_at: datetime
    updated_at: datetime


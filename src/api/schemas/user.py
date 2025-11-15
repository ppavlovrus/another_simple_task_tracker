"""User Pydantic schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    """Request model for creating a new user."""

    username: str
    email: str
    password: str


class UserUpdate(BaseModel):
    """Request model for updating a user."""

    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    """Response model for user data."""

    id: int
    username: str
    email: str
    created_at: datetime
    last_login: Optional[datetime] = None


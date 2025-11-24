"""Tags API endpoints."""
import asyncpg
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas.tags import TagCreate, TagResponse
from dependencies import get_db_connection

router = APIRouter(prefix="/tags", tags=["tags"])

@router.post("/", response_model=TagResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Create a new tag",
             description="Create a new tag with a name")
async def create_tag(tag: TagCreate, conn: Annotated[asyncpg.Connection, Depends(get_db_connection)]):
    try:
        await conn.execute("INSERT INTO tags (name) VALUES ($1)", tag.name)
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag already exists.")
    return tag
"""Tags API endpoints."""
import asyncpg
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Response

from api.schemas.tags import TagCreate, TagResponse
from dependencies import get_db_connection

router = APIRouter(prefix="/tags", tags=["tags"])


@router.post(
    "/",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tag",
    description="Create a new tag with a name",
)
async def create_tag(
    tag: TagCreate,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> TagResponse:
    try:
        row = await conn.fetchrow(
            "INSERT INTO tag (name) VALUES ($1) RETURNING id, name",
            tag.name,
        )
        return TagResponse(id=row["id"], name=row["name"])  # type: ignore[arg-type]
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tag with this name already exists",
        )
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get(
    "/",
    response_model=list[TagResponse],
    summary="List all tags",
)
async def list_tags(
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> list[TagResponse]:
    rows = await conn.fetch("SELECT id, name FROM tag ORDER BY id")
    return [TagResponse(id=r["id"], name=r["name"]) for r in rows]


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tag by ID",
)
async def delete_tag(
    tag_id: int,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> Response:
    row = await conn.fetchrow("DELETE FROM tag WHERE id = $1 RETURNING id", tag_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tag with id {tag_id} not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

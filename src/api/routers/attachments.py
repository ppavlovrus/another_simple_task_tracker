"""Attachment API endpoints."""
import asyncpg
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Response

from api.schemas.attachment import AttachmentCreate, AttachmentResponse
from dependencies import get_db_connection

router = APIRouter(prefix="/attachments", tags=["attachments"])

@router.post("/", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def create_attachment(
    attachment: AttachmentCreate,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> AttachmentResponse:
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO attachment (task_id, filename, content_type, storage_path, size_bytes)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, task_id, filename, content_type, storage_path, size_bytes, uploaded_at
            """,
            attachment.task_id,
            attachment.filename,
            attachment.content_type,
            attachment.storage_path,
            attachment.size_bytes,
        )
        return AttachmentResponse(**dict(row))
    except asyncpg.ForeignKeyViolationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task_id: task does not exist")
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(attachment_id: int, conn: Annotated[asyncpg.Connection, Depends(get_db_connection)]) -> Response:
    row = await conn.fetchrow("DELETE FROM attachment WHERE id = $1 RETURNING id", attachment_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Attachment with id {attachment_id} not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment(
    attachment_id: int,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> AttachmentResponse:
    row = await conn.fetchrow(
        """
        SELECT id, task_id, filename, content_type, storage_path, size_bytes, uploaded_at
        FROM attachment
        WHERE id = $1
        """,
        attachment_id,
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Attachment with id {attachment_id} not found")
    return AttachmentResponse(**dict(row))


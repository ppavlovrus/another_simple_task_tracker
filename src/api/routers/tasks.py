"""Task API endpoints."""
import asyncpg
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from dependencies import get_db_connection

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="Create a new task with optional assignees and deadlines",
)
async def create_task(
    task: TaskCreate,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> TaskResponse:
    """Create a new task in the database.

    Args:
        task: Task creation data
        conn: Database connection from pool

    Returns:
        Created task data

    Raises:
        HTTPException: If task creation fails or foreign key constraint violated
    """
    try:
        # Insert task into database
        row = await conn.fetchrow(
            """
            INSERT INTO task (title, description, status_id, creator_id, deadline_start, deadline_end)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, title, description, status_id, creator_id, deadline_start, deadline_end, created_at, updated_at
            """,
            task.title,
            task.description,
            task.status_id,
            task.creator_id,
            task.deadline_start,
            task.deadline_end,
        )

        if not row:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create task",
            )

        return TaskResponse(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status_id=row["status_id"],
            creator_id=row["creator_id"],
            deadline_start=row["deadline_start"],
            deadline_end=row["deadline_end"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    except asyncpg.ForeignKeyViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid foreign key reference: {e}",
        )
    except asyncpg.UniqueViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Unique constraint violation: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}",
        )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task by ID",
    description="Retrieve a task with its assignees by task ID",
)
async def get_task(
    task_id: int,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> TaskResponse:
    """Get task by ID from database.

    Args:
        task_id: Task identifier
        conn: Database connection from pool

    Returns:
        Task data with assignees

    Raises:
        HTTPException: If task not found
    """
    # Fetch task from database
    task_row = await conn.fetchrow(
        """
        SELECT id, title, description, status_id, creator_id,
               deadline_start, deadline_end, created_at, updated_at
        FROM task
        WHERE id = $1
        """,
        task_id,
    )

    if not task_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )

    return TaskResponse(
        id=task_row["id"],
        title=task_row["title"],
        description=task_row["description"],
        status_id=task_row["status_id"],
        creator_id=task_row["creator_id"],
        deadline_start=task_row["deadline_start"],
        deadline_end=task_row["deadline_end"],
        created_at=task_row["created_at"],
        updated_at=task_row["updated_at"],
    )


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task by ID",
    description="Update a task with its assignees by task ID",
)
async def update_task(
    task_id: int,
    task: TaskUpdate,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> TaskResponse:
    """Update task by ID in database.

    Args:
        task_id: Task identifier
        task: Task update data
        conn: Database connection from pool

    Returns:
        Updated task data

    Raises:
        HTTPException: If task update fails or foreign key constraint violated
    """
    try:
        # Validate that at least one field is provided
        if not any([
            task.title is not None,
            task.description is not None,
            task.status_id is not None,
            task.deadline_start is not None,
            task.deadline_end is not None,
        ]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field must be provided for update",
            )

        # Build dynamic UPDATE query with only non-None fields
        update_fields = []
        values = []
        param_index = 1

        if task.title is not None:
            update_fields.append(f"title = ${param_index}")
            values.append(task.title)
            param_index += 1

        if task.description is not None:
            update_fields.append(f"description = ${param_index}")
            values.append(task.description)
            param_index += 1

        if task.status_id is not None:
            update_fields.append(f"status_id = ${param_index}")
            values.append(task.status_id)
            param_index += 1

        if task.deadline_start is not None:
            update_fields.append(f"deadline_start = ${param_index}")
            values.append(task.deadline_start)
            param_index += 1

        if task.deadline_end is not None:
            update_fields.append(f"deadline_end = ${param_index}")
            values.append(task.deadline_end)
            param_index += 1

        # Always update updated_at
        update_fields.append("updated_at = NOW()")

        # Add task_id as last parameter
        values.append(task_id)

        # Build and execute query
        query = f"""
            UPDATE task
            SET {', '.join(update_fields)}
            WHERE id = ${param_index}
            RETURNING id, title, description, status_id, creator_id, deadline_start, deadline_end, created_at, updated_at
        """

        row = await conn.fetchrow(query, *values)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found",
            )

        return TaskResponse(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status_id=row["status_id"],
            creator_id=row["creator_id"],
            deadline_start=row["deadline_start"],
            deadline_end=row["deadline_end"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    except asyncpg.ForeignKeyViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid foreign key reference: {e}",
        )
    except asyncpg.UniqueViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Unique constraint violation: {e}",
        )
    except HTTPException:
        # Preserve already formed HTTPException (e.g., 404 not found)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}",
        )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task by ID",
    description="Delete a task by task ID",
)
async def delete_task(
    task_id: int,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> None:
    """Delete task by ID from database.

    Args:
        task_id: Task identifier
        conn: Database connection from pool

    Returns:
        None

    Raises:
        HTTPException: If task deletion fails or foreign key constraint violated
    """
    try:
        # Delete task from database and check if it existed
        deleted_id = await conn.fetchval(
            """
            DELETE FROM task WHERE id = $1
            RETURNING id
            """,
            task_id,
        )

        if deleted_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found",
            )
    except asyncpg.ForeignKeyViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid foreign key reference: {e}",
        )
    except HTTPException:
        # Preserve already formed HTTPException (e.g., 404 not found)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}",
        )


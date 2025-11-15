"""FastAPI application for Task Tracker.

This module provides REST API endpoints for task management using
FastAPI and asyncpg for asynchronous PostgreSQL database operations.
"""

import asyncpg
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Annotated, List, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel

# Application configuration
DATABASE_URL = "postgresql://user:password@localhost/task_tracker"

# Global connection pool
db_pool: Optional[asyncpg.Pool] = None


# Pydantic models for request/response validation
class TaskCreate(BaseModel):
    """Request model for creating a new task."""

    title: str
    description: Optional[str] = None
    status_id: int
    creator_id: int
    assignee_id: Optional[int] = None  # Single assignee (matches DB schema)
    deadline_start: Optional[date] = None
    deadline_end: Optional[date] = None


class TaskResponse(BaseModel):
    """Response model for task data."""

    id: int
    title: str
    description: Optional[str]
    status_id: int
    creator_id: int
    assignee_id: Optional[int]
    deadline_start: Optional[date]
    deadline_end: Optional[date]
    created_at: datetime
    updated_at: datetime


# Database connection pool lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database connection pool lifecycle.

    Creates connection pool on startup and closes it on shutdown.
    This ensures efficient connection reuse across requests.

    Args:
        app: FastAPI application instance
    """
    global db_pool

    # Startup: create connection pool
    db_pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=10,
        max_size=20,
        command_timeout=60,
        max_queries=50000,
        max_inactive_connection_lifetime=300.0,
    )
    print("Database connection pool created")

    yield

    # Shutdown: close connection pool
    await db_pool.close()
    print("Database connection pool closed")


# FastAPI application initialization
app = FastAPI(
    title="Task Tracker API",
    description="REST API for task management system",
    version="1.0.0",
    lifespan=lifespan,
)


# Dependency injection for database connections
async def get_db_connection() -> asyncpg.Connection:
    """Get database connection from pool.

    This dependency provides a connection from the connection pool.
    The connection is automatically returned to the pool after use.

    Yields:
        Database connection from pool

    Raises:
        HTTPException: If connection pool is not initialized
    """
    if db_pool is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection pool not initialized",
        )

    async with db_pool.acquire() as connection:
        yield connection


# API endpoints
@app.post(
    "/tasks",
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
            INSERT INTO tasks (title, description, status_id, creator_id, assignee_id, deadline_start, deadline_end)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, title, description, status_id, creator_id, assignee_id, deadline_start, deadline_end, created_at, updated_at
            """,
            task.title,
            task.description,
            task.status_id,
            task.creator_id,
            task.assignee_id,
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
            assignee_id=row["assignee_id"],
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


@app.get(
    "/tasks/{task_id}",
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
        SELECT id, title, description, status_id, creator_id, assignee_id,
               deadline_start, deadline_end, created_at, updated_at
        FROM tasks
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
        assignee_id=task_row["assignee_id"],
        deadline_start=task_row["deadline_start"],
        deadline_end=task_row["deadline_end"],
        created_at=task_row["created_at"],
        updated_at=task_row["updated_at"],
    )


# Application entry point
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
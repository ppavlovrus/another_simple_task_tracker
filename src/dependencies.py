"""FastAPI dependencies."""
import asyncpg
from fastapi import HTTPException, status

from application.services import get_pool


async def get_db_connection() -> asyncpg.Connection:
    """Get database connection from pool.

    This dependency provides a connection from the connection pool.
    The connection is automatically returned to the pool after use.

    Yields:
        Database connection from pool

    Raises:
        HTTPException: If connection pool is not initialized
    """
    pool = get_pool()
    if pool is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection pool not initialized",
        )

    async with pool.acquire() as connection:
        yield connection


"""User API endpoints."""
import asyncpg
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas.user import UserCreate, UserResponse, UserUpdate
from dependencies import get_db_connection

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user with username, email, and password",
)
async def create_user(
    user: UserCreate,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> UserResponse:
    """Create a new user in the database.

    Args:
        user: User creation data
        conn: Database connection from pool

    Returns:
        Created user data

    Raises:
        HTTPException: If user creation fails or unique constraint violated
    """
    try:
        # TODO: Hash password before storing (use bcrypt or similar)
        # For now, storing as plain text (NOT SECURE - for development only)
        row = await conn.fetchrow(
            """
            INSERT INTO "user" (username, email, password_hash)
            VALUES ($1, $2, $3)
            RETURNING id, username, email, created_at, last_login
            """,
            user.username,
            user.email,
            user.password,  # TODO: Replace with hashed password
        )

        if not row:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user",
            )

        return UserResponse(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            created_at=row["created_at"],
            last_login=row["last_login"],
        )

    except asyncpg.UniqueViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with this username or email already exists: {e}",
        )
    except HTTPException:
        # Preserve previously raised HTTP errors
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}",
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve a user by user ID",
)
async def get_user(
    user_id: int,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> UserResponse:
    """Get user by ID from database.

    Args:
        user_id: User identifier
        conn: Database connection from pool

    Returns:
        User data

    Raises:
        HTTPException: If user not found
    """
    try:
        row = await conn.fetchrow(
            """
            SELECT id, username, email, created_at, last_login
            FROM "user"
            WHERE id = $1
            """,
            user_id,
        )

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        return UserResponse(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            created_at=row["created_at"],
            last_login=row["last_login"],
        )
    except HTTPException:
        # Preserve expected HTTP statuses like 404
        raise
    except Exception as e:
        # Convert unexpected errors to 500 for stable API contract
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}",
        )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user by ID",
    description="Update a user by user ID",
)
async def update_user(
    user_id: int,
    user: UserUpdate,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> UserResponse:
    """Update user by ID in database.

    Args:
        user_id: User identifier
        user: User update data
        conn: Database connection from pool

    Returns:
        Updated user data

    Raises:
        HTTPException: If user update fails or unique constraint violated
    """
    try:
        # Validate that at least one field is provided
        if not any([
            user.username is not None,
            user.email is not None,
            user.password is not None,
        ]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field must be provided for update",
            )

        # Build dynamic UPDATE query with only non-None fields
        update_fields = []
        values = []
        param_index = 1

        if user.username is not None:
            update_fields.append(f"username = ${param_index}")
            values.append(user.username)
            param_index += 1

        if user.email is not None:
            update_fields.append(f"email = ${param_index}")
            values.append(user.email)
            param_index += 1

        if user.password is not None:
            # TODO: Hash password before storing
            update_fields.append(f"password_hash = ${param_index}")
            values.append(user.password)  # TODO: Replace with hashed password
            param_index += 1

        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field must be provided for update",
            )

        # Add user_id as last parameter
        values.append(user_id)

        # Build and execute query
        query = f"""
            UPDATE "user"
            SET {', '.join(update_fields)}
            WHERE id = ${param_index}
            RETURNING id, username, email, created_at, last_login
        """

        row = await conn.fetchrow(query, *values)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        return UserResponse(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            created_at=row["created_at"],
            last_login=row["last_login"],
        )

    except asyncpg.UniqueViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with this username or email already exists: {e}",
        )
    except HTTPException:
        # Preserve previously raised HTTP errors (e.g., 400 for missing fields, 404 not found)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}",
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user by ID",
    description="Delete a user by user ID",
)
async def delete_user(
    user_id: int,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> None:
    """Delete user by ID from database.

    Args:
        user_id: User identifier
        conn: Database connection from pool

    Returns:
        None

    Raises:
        HTTPException: If user deletion fails or foreign key constraint violated
    """
    try:
        # Delete user from database and check if it existed
        deleted_id = await conn.fetchval(
            """
            DELETE FROM "user" WHERE id = $1
            RETURNING id
            """,
            user_id,
        )

        if deleted_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

    except asyncpg.ForeignKeyViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete user: {e}",
        )
    except HTTPException:
        # Keep previously raised 404 not found as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}",
        )


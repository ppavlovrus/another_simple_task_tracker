"""Authentication API endpoints."""
import asyncpg
from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.schemas.auth import (
    AuthLogin,
    AuthRegister,
    AuthRefresh,
    AuthLogout,
    AuthResponse,
    LogoutResponse,
)
from dependencies import get_db_connection
from config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from utils.jwt import create_access_token, create_refresh_token, decode_token, verify_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate user with username and password, return JWT tokens",
)
async def login(
    login_data: AuthLogin,
    request: Request,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> AuthResponse:
    """Authenticate user and create session.

    Args:
        login_data: User login credentials
        request: FastAPI request object (for IP and User-Agent)
        conn: Database connection from pool

    Returns:
        Authentication response with JWT tokens

    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Find user by username
        user_row = await conn.fetchrow(
            """
            SELECT id, username, email, password_hash
            FROM "user"
            WHERE username = $1
            """,
            login_data.username,
        )

        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        # TODO: Verify password hash using bcrypt/passlib
        # For now, comparing plain text (NOT SECURE - for development only)
        if user_row["password_hash"] != login_data.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        # Get client IP and User-Agent
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Calculate token expiration times
        refresh_token_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        # Create auth session in database first (to get session_id)
        session_row = await conn.fetchrow(
            """
            INSERT INTO auth_session (user_id, ip_address, user_agent, expires_at)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            user_row["id"],
            client_ip,
            user_agent,
            refresh_token_expires,
        )

        if not session_row:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session",
            )

        session_id = UUID(str(session_row["id"]))

        # Generate JWT tokens using session_id
        access_token = create_access_token(
            user_id=user_row["id"],
            session_id=session_id,
        )
        refresh_token = create_refresh_token(
            session_id=session_id,
        )

        # Update last_login timestamp
        await conn.execute(
            """
            UPDATE "user"
            SET last_login = NOW()
            WHERE id = $1
            """,
            user_row["id"],
        )

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}",
        )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User registration",
    description="Register a new user and return JWT tokens",
)
async def register(
    register_data: AuthRegister,
    request: Request,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> AuthResponse:
    """Register a new user and create session.

    Args:
        register_data: User registration data
        request: FastAPI request object (for IP and User-Agent)
        conn: Database connection from pool

    Returns:
        Authentication response with JWT tokens

    Raises:
        HTTPException: If registration fails
    """
    try:
        # TODO: Hash password using bcrypt/passlib before storing
        # For now, storing as plain text (NOT SECURE - for development only)
        password_hash = register_data.password  # TODO: Replace with hashed password

        # Create user
        user_row = await conn.fetchrow(
            """
            INSERT INTO "user" (username, email, password_hash)
            VALUES ($1, $2, $3)
            RETURNING id, username, email
            """,
            register_data.username,
            register_data.email,
            password_hash,
        )

        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user",
            )

        # Get client IP and User-Agent
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Calculate token expiration times
        refresh_token_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        # Create auth session first (to get session_id)
        session_row = await conn.fetchrow(
            """
            INSERT INTO auth_session (user_id, ip_address, user_agent, expires_at)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            user_row["id"],
            client_ip,
            user_agent,
            refresh_token_expires,
        )

        if not session_row:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session",
            )

        session_id = UUID(str(session_row["id"]))

        # Generate JWT tokens using session_id
        access_token = create_access_token(
            user_id=user_row["id"],
            session_id=session_id,
        )
        refresh_token = create_refresh_token(
            session_id=session_id,
        )

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except asyncpg.UniqueViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with this username or email already exists: {e}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}",
        )


@router.post(
    "/refresh",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Exchange refresh token for new access and refresh tokens",
)
async def refresh(
    refresh_data: AuthRefresh,
    request: Request,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> AuthResponse:
    """Refresh access token using refresh token.

    Args:
        refresh_data: Refresh token data
        request: FastAPI request object
        conn: Database connection from pool

    Returns:
        New authentication response with JWT tokens

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    try:
        # Decode and verify refresh token
        payload = verify_token(refresh_data.refresh_token, token_type="refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        # Get session_id from token payload
        session_id = UUID(payload["session_id"])

        # Verify session exists and is valid in database
        session_row = await conn.fetchrow(
            """
            SELECT id, user_id, expires_at
            FROM auth_session
            WHERE id = $1
            AND expires_at > NOW()
            """,
            session_id,
        )

        if not session_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid",
            )

        # Calculate new expiration times
        refresh_token_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        # Generate new JWT tokens
        access_token = create_access_token(
            user_id=session_row["user_id"],
            session_id=session_id,
        )
        new_refresh_token = create_refresh_token(
            session_id=session_id,
        )

        # Update session expiration
        await conn.execute(
            """
            UPDATE auth_session
            SET expires_at = $1
            WHERE id = $2
            """,
            refresh_token_expires,
            session_id,
        )

        return AuthResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}",
        )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Invalidate user session and logout",
)
async def logout(
    logout_data: AuthLogout,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> LogoutResponse:
    """Logout user and invalidate session.

    Args:
        logout_data: Logout data (optional refresh token)
        conn: Database connection from pool

    Returns:
        Logout confirmation response

    Raises:
        HTTPException: If logout fails
    """
    try:
        if logout_data.refresh_token:
            # Decode refresh token to get session_id
            payload = decode_token(logout_data.refresh_token)
            if payload and payload.get("type") == "refresh":
                session_id = UUID(payload["session_id"])

                # Delete session from database
                await conn.execute(
                    """
                    DELETE FROM auth_session
                    WHERE id = $1
                    """,
                    session_id,
                )

        return LogoutResponse(message="Successfully logged out")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}",
        )

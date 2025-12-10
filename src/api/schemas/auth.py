"""Authentication Pydantic schemas."""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class AuthLogin(BaseModel):
    """Request model for user login.

    Args:
        username: User username
        password: User password
    """

    username: str = Field(..., min_length=3, max_length=64, description="User username")
    password: str = Field(..., min_length=6, description="User password")


class AuthRegister(BaseModel):
    """Request model for user registration.

    Args:
        username: User username (3-64 characters)
        email: User email address
        password: User password (minimum 6 characters)
    """

    username: str = Field(..., min_length=3, max_length=64, description="User username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not v.strip():
            raise ValueError("Username cannot be empty or whitespace only")
        return v.strip()


class AuthRefresh(BaseModel):
    """Request model for token refresh.

    Args:
        refresh_token: Refresh token to exchange for new access token
    """

    refresh_token: str = Field(..., description="Refresh token")


class AuthLogout(BaseModel):
    """Request model for user logout.

    Args:
        refresh_token: Refresh token to invalidate (optional)
    """

    refresh_token: Optional[str] = Field(None, description="Refresh token to invalidate")


class AuthResponse(BaseModel):
    """Response model for authentication operations.

    Args:
        access_token: JWT access token
        refresh_token: JWT refresh token
        token_type: Token type (default: "Bearer")
        expires_in: Token expiration time in seconds
    """

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class LogoutResponse(BaseModel):
    """Response model for logout operation.

    Args:
        message: Logout confirmation message
    """

    message: str = Field(default="Successfully logged out", description="Logout message")

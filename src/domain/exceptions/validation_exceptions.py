"""General validation related domain exceptions."""

from .base import DomainException


class ValidationError(DomainException):
    """Base exception for validation errors.

    This is a general validation exception that can be used
    when a more specific validation exception is not available.
    """

    def __init__(self, message: str, field: str | None = None) -> None:
        """Initialize validation error.

        Args:
            message: Error message
            field: Optional field name that failed validation
        """
        super().__init__(message, error_code="VALIDATION_ERROR")
        self.field = field


class InvalidEmailError(ValidationError):
    """Raised when email format is invalid.

    This exception is raised when email validation fails.
    """

    def __init__(self, email: str) -> None:
        """Initialize invalid email error.

        Args:
            email: Invalid email address
        """
        message = f"Invalid email format: {email}"
        super().__init__(message, field="email")
        self.error_code = "INVALID_EMAIL"
        self.email = email


class InvalidDurationError(ValidationError):
    """Raised when duration value is invalid.

    This exception is raised when time log duration is negative
    or exceeds reasonable limits.
    """

    def __init__(
        self,
        duration_seconds: int,
        reason: str | None = None,
    ) -> None:
        """Initialize invalid duration error.

        Args:
            duration_seconds: Invalid duration value
            reason: Optional reason why duration is invalid
        """
        if reason:
            message = f"Invalid duration: {duration_seconds} seconds. {reason}"
        else:
            message = f"Invalid duration: {duration_seconds} seconds (must be positive)"
        super().__init__(message, field="duration_seconds")
        self.error_code = "INVALID_DURATION"
        self.duration_seconds = duration_seconds
        self.reason = reason


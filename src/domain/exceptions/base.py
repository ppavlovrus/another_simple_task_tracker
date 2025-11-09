"""Base domain exception class.

All domain-specific exceptions should inherit from this base class.
"""


class DomainException(Exception):
    """Base exception for all domain-related errors.

    This exception serves as a base class for all domain-specific
    exceptions, allowing for centralized exception handling and
    providing a common interface for error messages.

    Attributes:
        message: Human-readable error message
        error_code: Optional error code for programmatic handling
    """

    def __init__(self, message: str, error_code: str | None = None) -> None:
        """Initialize domain exception.

        Args:
            message: Human-readable error message
            error_code: Optional error code for programmatic handling
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code

    def __str__(self) -> str:
        """Return string representation of exception."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def __repr__(self) -> str:
        """Return detailed representation of exception."""
        return f"{self.__class__.__name__}(message={self.message!r}, error_code={self.error_code!r})"


"""Email value object for user email addresses."""

import re
from typing import Any

from domain.exceptions.validation_exceptions import InvalidEmailError


class Email:
    """Represents an email address as a value object.

    This value object ensures email addresses are:
    - Validated according to RFC 5322 compliant pattern
    - Normalized (lowercase, trimmed)
    - Immutable after creation

    Attributes:
        value: The normalized email address string
    """

    # RFC 5322 compliant email regex pattern
    EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    def __init__(self, email: str) -> None:
        """Initialize Email instance.

        Args:
            email: Email address to validate and normalize

        Raises:
            InvalidEmailError: If email format is invalid
        """
        if not email or not email.strip():
            raise InvalidEmailError(email)

        normalized = email.strip().lower()

        if not self._validate(normalized):
            raise InvalidEmailError(email)

        self._value = normalized

    @classmethod
    def _validate(cls, email: str) -> bool:
        """Validate email address format.

        Args:
            email: Email address to validate

        Returns:
            True if email format is valid
        """
        return bool(cls.EMAIL_PATTERN.match(email))

    @property
    def value(self) -> str:
        """Get the normalized email address value.

        Returns:
            Normalized email address string
        """
        return self._value

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return f"Email(value={self._value!r})"

    def __str__(self) -> str:
        """Return email address as string."""
        return self._value

    def __eq__(self, other: Any) -> bool:
        """Check equality with another Email instance.

        Args:
            other: Object to compare with

        Returns:
            True if emails are equal (case-insensitive)
        """
        if not isinstance(other, Email):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        """Return hash of email value for use in sets/dicts.

        Returns:
            Hash of the email value
        """
        return hash(self._value)
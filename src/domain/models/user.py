"""User domain model."""

from datetime import datetime

from domain.value_objects.email import Email


class User:
    """User entity representing a system user.

    Attributes:
        id: Unique identifier
        name: User's full name
        email: Email Value Object (validated and normalized)
        password: Hashed password
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    def __init__(
        self,
        id: int,
        name: str,
        email: Email,
        password: str,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        """Initialize User instance.

        Args:
            id: Unique identifier
            name: User's full name
            email: Email Value Object (validated and normalized)
            password: Hashed password
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.created_at = created_at
        self.updated_at = updated_at

    def update_email(self, new_email: Email) -> None:
        """Update user email.

        Args:
            new_email: New Email Value Object (already validated)
        """
        self.email = new_email

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"User(id={self.id}, name={self.name!r}, "
            f"email={self.email.value}, created_at={self.created_at}, "
            f"updated_at={self.updated_at})"
        )

    def __str__(self) -> str:
        """Return human-readable string representation."""
        return f"User(id={self.id}, name={self.name}, email={self.email.value})"
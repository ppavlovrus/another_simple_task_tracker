"""Comment model for task comments.

This module contains the Comment model for implementing
comment functionality (FR-3.1, FR-3.2, FR-3.3).
"""

from datetime import datetime


class Comment:
    """Represents a comment on a task.

    According to FR-3.1, FR-3.2, FR-3.3:
    - Any authorized user can add a comment to a task
    - Comments are immutable after creation (or can be edited with history)
    - Comments are displayed in chronological order

    Attributes:
        id: Unique identifier for the comment
        task_id: ID of the task this comment relates to
        user_id: ID of the user who added the comment
        content: The text content of the comment
        created_at: Timestamp when comment was created
    """

    def __init__(
        self,
        id: int,
        task_id: int,
        user_id: int,
        content: str,
        created_at: datetime,
    ) -> None:
        """Initialize Comment instance.

        Args:
            id: Unique identifier for the comment
            task_id: ID of the task this comment relates to
            user_id: ID of the user who added the comment
            content: The text content of the comment
            created_at: Timestamp when comment was created
        """
        self.id = id
        self.task_id = task_id
        self.user_id = user_id
        self.content = content
        self.created_at = created_at

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"Comment(id={self.id}, task_id={self.task_id}, "
            f"user_id={self.user_id}, content={self.content[:50]!r}..., "
            f"created_at={self.created_at})"
        )

    def __str__(self) -> str:
        """Return human-readable string representation."""
        return (
            f"Comment(id={self.id}, task_id={self.task_id}, "
            f"user_id={self.user_id}, created_at={self.created_at})"
        )
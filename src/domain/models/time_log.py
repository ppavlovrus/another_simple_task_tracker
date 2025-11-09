"""TimeLog domain model."""

from datetime import datetime
from typing import Optional

from domain.value_objects.duration import Duration


class TimeLog:
    """TimeLog entity representing time spent on a task.

    According to FR-2.1, time logs track:
    - Duration in seconds
    - Optional comment
    - User who logged the time
    - Timestamp when time was logged

    Attributes:
        id: Unique identifier
        task_id: ID of related task
        user_id: ID of user who logged time
        duration: Duration Value Object (validated)
        comment: Optional comment about the time spent
        logged_at: Timestamp when time was logged
    """

    def __init__(
        self,
        id: int,
        task_id: int,
        user_id: int,
        duration: Duration,
        comment: Optional[str],
        logged_at: datetime,
    ) -> None:
        """Initialize TimeLog instance.

        Args:
            id: Unique identifier
            task_id: ID of related task
            user_id: ID of user who logged time
            duration: Duration Value Object (validated)
            comment: Optional comment about the time spent
            logged_at: Timestamp when time was logged
        """
        self.id = id
        self.task_id = task_id
        self.user_id = user_id
        self.duration = duration
        self.comment = comment
        self.logged_at = logged_at

    def get_duration_hours(self) -> float:
        """Get duration in hours.

        Returns:
            Duration in hours as float
        """
        return self.duration.hours

    def get_duration_minutes(self) -> float:
        """Get duration in minutes.

        Returns:
            Duration in minutes as float
        """
        return self.duration.minutes

    def get_duration_seconds(self) -> int:
        """Get duration in seconds.

        Returns:
            Duration in seconds as int
        """
        return self.duration.seconds

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"TimeLog(id={self.id}, task_id={self.task_id}, "
            f"user_id={self.user_id}, duration={self.duration.seconds}s, "
            f"comment={self.comment!r}, logged_at={self.logged_at})"
        )

    def __str__(self) -> str:
        """Return human-readable string representation."""
        return (
            f"TimeLog(id={self.id}, task_id={self.task_id}, "
            f"duration={self.duration}, logged_at={self.logged_at})"
        )
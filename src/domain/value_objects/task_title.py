"""TaskTitle value object for task titles."""

from typing import Any

from domain.exceptions.task_exceptions import TaskTitleTooLongError


class TaskTitle:
    """Represents a task title as a value object.

    According to FR-1.1, task title must be:
    - Non-empty string
    - Maximum 255 characters

    Attributes:
        value: The validated title string
    """

    MAX_LENGTH = 255

    def __init__(self, title: str) -> None:
        """Initialize TaskTitle instance.

        Args:
            title: Task title to validate

        Raises:
            ValueError: If title is empty or whitespace only
            TaskTitleTooLongError: If title exceeds maximum length
        """
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")

        normalized = title.strip()

        if len(normalized) > self.MAX_LENGTH:
            raise TaskTitleTooLongError(len(normalized), self.MAX_LENGTH)

        self._value = normalized

    @property
    def value(self) -> str:
        """Get the normalized task title value.

        Returns:
            Normalized task title string
        """
        return self._value

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return f"TaskTitle(value={self._value!r})"

    def __str__(self) -> str:
        """Return task title as string."""
        return self._value

    def __eq__(self, other: Any) -> bool:
        """Check equality with another TaskTitle instance.

        Args:
            other: Object to compare with

        Returns:
            True if titles are equal
        """
        if not isinstance(other, TaskTitle):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        """Return hash of title value for use in sets/dicts.

        Returns:
            Hash of the title value
        """
        return hash(self._value)
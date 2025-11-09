"""Task-related domain exceptions."""

from .base import DomainException


class TaskNotFoundError(DomainException):
    """Raised when a task is not found in the repository.

    This exception is raised when attempting to access or modify
    a task that does not exist or has been deleted.
    """

    def __init__(self, task_id: int | None = None) -> None:
        """Initialize task not found error.

        Args:
            task_id: Optional task ID that was not found
        """
        if task_id is not None:
            message = f"Task with ID {task_id} not found"
        else:
            message = "Task not found"
        super().__init__(message, error_code="TASK_NOT_FOUND")
        self.task_id = task_id


class TaskAlreadyArchivedError(DomainException):
    """Raised when attempting to modify an archived task.

    This exception is raised when trying to edit, change status,
    or perform other operations on a task that has been archived.
    """

    def __init__(self, task_id: int) -> None:
        """Initialize task already archived error.

        Args:
            task_id: ID of the archived task
        """
        message = f"Task {task_id} is archived and cannot be modified"
        super().__init__(message, error_code="TASK_ALREADY_ARCHIVED")
        self.task_id = task_id


class InvalidTaskStatusTransitionError(DomainException):
    """Raised when attempting an invalid status transition.

    This exception is raised when trying to change task status
    in a way that violates business rules (e.g., from CANCELLED
    to IN_PROGRESS).
    """

    def __init__(
        self,
        current_status: str,
        target_status: str,
        task_id: int | None = None,
    ) -> None:
        """Initialize invalid status transition error.

        Args:
            current_status: Current task status
            target_status: Target task status that is invalid
            task_id: Optional task ID
        """
        task_info = f" for task {task_id}" if task_id else ""
        message = (
            f"Invalid status transition from '{current_status}' "
            f"to '{target_status}'{task_info}"
        )
        super().__init__(message, error_code="INVALID_STATUS_TRANSITION")
        self.current_status = current_status
        self.target_status = target_status
        self.task_id = task_id


class TaskTitleTooLongError(DomainException):
    """Raised when task title exceeds maximum length.

    According to FR-1.1, task title must be ≤ 255 characters.
    """

    def __init__(self, title_length: int, max_length: int = 255) -> None:
        """Initialize task title too long error.

        Args:
            title_length: Actual length of the title
            max_length: Maximum allowed length (default: 255)
        """
        message = (
            f"Task title length ({title_length}) exceeds "
            f"maximum allowed length ({max_length} characters)"
        )
        super().__init__(message, error_code="TASK_TITLE_TOO_LONG")
        self.title_length = title_length
        self.max_length = max_length


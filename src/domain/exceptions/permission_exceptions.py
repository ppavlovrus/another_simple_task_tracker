"""Permission and authorization related domain exceptions."""

from .base import DomainException


class PermissionDeniedError(DomainException):
    """Raised when user lacks required permissions.

    This is a general permission error that can be used when
    a more specific permission exception is not available.
    """

    def __init__(self, action: str, resource: str | None = None) -> None:
        """Initialize permission denied error.

        Args:
            action: Action that was denied (e.g., 'edit', 'delete')
            resource: Optional resource name (e.g., 'task', 'comment')
        """
        if resource:
            message = f"Permission denied: cannot {action} {resource}"
        else:
            message = f"Permission denied: cannot {action}"
        super().__init__(message, error_code="PERMISSION_DENIED")
        self.action = action
        self.resource = resource


class UnauthorizedTaskEditError(DomainException):
    """Raised when user is not authorized to edit a task.

    According to FR-1.2, only creator, assignee, or admin can edit tasks.
    This exception is raised when a user who is not one of these
    attempts to modify a task.
    """

    def __init__(self, task_id: int | None = None, user_id: int | None = None) -> None:
        """Initialize unauthorized task edit error.

        Args:
            task_id: Optional task ID that user tried to edit
            user_id: Optional user ID who attempted the edit
        """
        message = "User is not authorized to edit this task"
        if task_id and user_id:
            message = f"User {user_id} is not authorized to edit task {task_id}"
        elif task_id:
            message = f"User is not authorized to edit task {task_id}"
        elif user_id:
            message = f"User {user_id} is not authorized to edit this task"

        super().__init__(message, error_code="UNAUTHORIZED_TASK_EDIT")
        self.task_id = task_id
        self.user_id = user_id


class UnauthorizedTaskDeletionError(DomainException):
    """Raised when user is not authorized to delete/archive a task.

    According to FR-5.2, only creator or admin can delete/archive tasks.
    """

    def __init__(self, task_id: int | None = None, user_id: int | None = None) -> None:
        """Initialize unauthorized task deletion error.

        Args:
            task_id: Optional task ID that user tried to delete
            user_id: Optional user ID who attempted the deletion
        """
        message = "User is not authorized to delete this task"
        if task_id and user_id:
            message = f"User {user_id} is not authorized to delete task {task_id}"
        elif task_id:
            message = f"User is not authorized to delete task {task_id}"
        elif user_id:
            message = f"User {user_id} is not authorized to delete this task"

        super().__init__(message, error_code="UNAUTHORIZED_TASK_DELETION")
        self.task_id = task_id
        self.user_id = user_id


class UnauthorizedAssigneeChangeError(DomainException):
    """Raised when user is not authorized to change task assignee.

    According to FR-5.2, only creator or admin can assign tasks.
    """

    def __init__(self, task_id: int | None = None, user_id: int | None = None) -> None:
        """Initialize unauthorized assignee change error.

        Args:
            task_id: Optional task ID
            user_id: Optional user ID who attempted the change
        """
        message = "User is not authorized to change task assignee"
        if task_id and user_id:
            message = (
                f"User {user_id} is not authorized to change "
                f"assignee for task {task_id}"
            )
        elif task_id:
            message = f"User is not authorized to change assignee for task {task_id}"
        elif user_id:
            message = f"User {user_id} is not authorized to change task assignee"

        super().__init__(message, error_code="UNAUTHORIZED_ASSIGNEE_CHANGE")
        self.task_id = task_id
        self.user_id = user_id


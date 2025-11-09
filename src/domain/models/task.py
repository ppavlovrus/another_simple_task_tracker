"""Task domain model."""

from enum import Enum
from typing import Optional

from domain.exceptions.permission_exceptions import (
    UnauthorizedAssigneeChangeError,
    UnauthorizedTaskEditError,
)
from domain.services.permission_service import PermissionService
from domain.services.task_status_service import TaskStatusService
from domain.value_objects.task_title import TaskTitle


class TaskStatus(str, Enum):
    """Task status enumeration.

    According to FR-1.1, possible statuses are:
    - CREATED: Task has been created
    - IN_PROGRESS: Task is being worked on
    - PAUSED: Task is temporarily paused
    - COMPLETED: Task is completed
    - CANCELLED: Task is cancelled
    """

    CREATED = "created"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task:
    """Task entity representing a work task.

    Attributes:
        id: Unique identifier
        title: TaskTitle Value Object (validated)
        description: Optional task description
        status: Current task status
        creator_id: ID of user who created the task
        assignee_id: Optional ID of assigned user
    """

    def __init__(
        self,
        id: int,
        title: TaskTitle,
        description: Optional[str],
        status: TaskStatus,
        creator_id: int,
        assignee_id: Optional[int] = None,
    ) -> None:
        """Initialize Task instance.

        Args:
            id: Unique identifier
            title: TaskTitle Value Object (validated)
            description: Optional task description
            status: Current task status
            creator_id: ID of user who created the task
            assignee_id: Optional ID of assigned user
        """
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.creator_id = creator_id
        self.assignee_id = assignee_id

    def update_title(
        self, new_title: TaskTitle, user_id: int, is_admin: bool = False
    ) -> None:
        """Update task title with permission check.

        According to FR-1.2 and FR-5.1, only creator, assignee, or admin
        can edit task title.

        Args:
            new_title: New TaskTitle Value Object (already validated)
            user_id: ID of user attempting to update
            is_admin: Whether user is administrator

        Raises:
            UnauthorizedTaskEditError: If user doesn't have permission
        """
        if not PermissionService.can_edit_task(
            user_id=user_id, task=self, is_admin=is_admin
        ):
            raise UnauthorizedTaskEditError(task_id=self.id, user_id=user_id)

        self.title = new_title

    def change_status(
        self, new_status: TaskStatus, user_id: int, is_admin: bool = False
    ) -> None:
        """Change task status with validation.

        According to FR-1.2 and FR-5.1, only creator, assignee, or admin
        can change task status. Status transition must be valid.

        Args:
            new_status: Target status
            user_id: ID of user attempting to change status
            is_admin: Whether user is administrator

        Raises:
            UnauthorizedTaskEditError: If user doesn't have permission
            InvalidTaskStatusTransitionError: If transition is not allowed
        """
        if not PermissionService.can_edit_task(
            user_id=user_id, task=self, is_admin=is_admin
        ):
            raise UnauthorizedTaskEditError(task_id=self.id, user_id=user_id)

        TaskStatusService.validate_transition(task=self, new_status=new_status)

        self.status = new_status

    def assign_to(
        self, assignee_id: int, user_id: int, is_admin: bool = False
    ) -> None:
        """Assign task to user with permission check.

        According to FR-5.2, only creator or admin can assign tasks.

        Args:
            assignee_id: ID of user to assign task to
            user_id: ID of user attempting to assign
            is_admin: Whether user is administrator

        Raises:
            UnauthorizedAssigneeChangeError: If user doesn't have permission
        """
        if not PermissionService.can_change_assignee(
            user_id=user_id, task=self, is_admin=is_admin
        ):
            raise UnauthorizedAssigneeChangeError(task_id=self.id, user_id=user_id)

        self.assignee_id = assignee_id

    def start_work(self, user_id: int, is_admin: bool = False) -> None:
        """Start working on task (change status to IN_PROGRESS).

        This is a convenience method that uses change_status internally.

        Args:
            user_id: ID of user starting work
            is_admin: Whether user is administrator

        Raises:
            UnauthorizedTaskEditError: If user doesn't have permission
            InvalidTaskStatusTransitionError: If transition is not allowed
        """
        self.change_status(
            new_status=TaskStatus.IN_PROGRESS, user_id=user_id, is_admin=is_admin
        )

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"Task(id={self.id}, title={self.title.value!r}, "
            f"status={self.status.value}, creator_id={self.creator_id}, "
            f"assignee_id={self.assignee_id})"
        )

    def __str__(self) -> str:
        """Return human-readable string representation."""
        return f"Task(id={self.id}, title={self.title.value})"
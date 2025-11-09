"""Activity model for tracking task-related events.

This module contains the Activity model and ActivityType enum
for implementing audit log functionality (FR-7.1, FR-7.2).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class ActivityType(str, Enum):
    """Types of activities that can be recorded in the audit log.

    According to FR-7.1, system should track:
    - Status changes
    - Comment additions
    - File attachments
    - Task creation/assignment/archiving
    """

    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"
    TASK_ASSIGNED = "task_assigned"
    TASK_UNASSIGNED = "task_unassigned"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_ARCHIVED = "task_archived"
    TASK_UNARCHIVED = "task_unarchived"
    COMMENT_ADDED = "comment_added"
    COMMENT_UPDATED = "comment_updated"
    COMMENT_DELETED = "comment_deleted"
    ATTACHMENT_ADDED = "attachment_added"
    ATTACHMENT_DELETED = "attachment_deleted"
    TIME_LOG_ADDED = "time_log_added"


class Activity:
    """Represents an activity/event in the task audit log.

    According to FR-7.1, system saves journal of events:
    - Who changed status
    - Who added comment/file
    - When task was created/assigned/archived

    Attributes:
        id: Unique identifier for the activity
        task_id: ID of the task this activity relates to
        user_id: ID of the user who performed the action
        activity_type: Type of activity (from ActivityType enum)
        activity_data: Additional data about the activity (JSON-serializable dict)
        created_at: Timestamp when activity was recorded
    """

    def __init__(
        self,
        id: int,
        task_id: int,
        user_id: int,
        activity_type: ActivityType,
        created_at: datetime,
        activity_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize Activity instance.

        Args:
            id: Unique identifier for the activity
            task_id: ID of the task this activity relates to
            user_id: ID of the user who performed the action
            activity_type: Type of activity (from ActivityType enum)
            created_at: Timestamp when activity was recorded
            activity_data: Optional additional data about the activity
        """
        self.id = id
        self.task_id = task_id
        self.user_id = user_id
        self.activity_type = activity_type
        self.created_at = created_at
        self.activity_data = activity_data or {}

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"Activity(id={self.id}, task_id={self.task_id}, "
            f"user_id={self.user_id}, activity_type={self.activity_type.value}, "
            f"created_at={self.created_at}, activity_data={self.activity_data})"
        )

    def __str__(self) -> str:
        """Return human-readable string representation."""
        return (
            f"Activity(id={self.id}, task_id={self.task_id}, "
            f"user_id={self.user_id}, activity_type={self.activity_type.value}, "
            f"created_at={self.created_at})"
        )

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from .task_status import TaskStatus

if TYPE_CHECKING:
    from .user import User
    from .attachment import Attachment
    from .tag import Tag    


@dataclass
class Task:
    # Required fields
    id: int
    title: str
    status_id: int
    creator_id: int
    created_at: datetime
    updated_at: datetime
    
    # Optional fields
    description: Optional[str] = None
    deadline_start: Optional[date] = None
    deadline_end: Optional[date] = None
    
    # Collections with defaults
    assignees: list["User"] = field(default_factory=list)
    attachments: list["Attachment"] = field(default_factory=list)
    tags: list["Tag"] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate task data after initialization."""
        if not self.title or not self.title.strip():
            raise ValueError("Task title cannot be empty or whitespace only")
        
        if self.deadline_start and self.deadline_end:
            if self.deadline_end < self.deadline_start:
                raise ValueError("deadline_end cannot be earlier than deadline_start")
        
        if len(self.title) > 255:
            raise ValueError("Task title cannot be longer than 255 characters")

    def is_overdue(self) -> bool:
        return self.deadline_end and self.deadline_end < date.today() 

    def is_completed(self) -> bool:
        return self.status_id == TaskStatus.DONE

    def is_cancelled(self) -> bool:
        return self.status_id == TaskStatus.CANCELLED

    def is_in_progress(self) -> bool:
        return self.status_id == TaskStatus.IN_PROGRESS

    def is_to_do(self) -> bool:
        return self.status_id == TaskStatus.TO_DO

    def can_be_completed(self) -> bool:
        return self.status_id == TaskStatus.TO_DO or self.status_id == TaskStatus.IN_PROGRESS

    def can_be_cancelled(self) -> bool:
        return self.status_id == TaskStatus.TO_DO or self.status_id == TaskStatus.IN_PROGRESS

    def can_be_in_progress(self) -> bool:
        return self.status_id == TaskStatus.TO_DO

    def can_be_to_do(self) -> bool:
        return self.status_id == TaskStatus.IN_PROGRESS

    def can_be_updated(self) -> bool:
        return self.status_id == TaskStatus.TO_DO or self.status_id == TaskStatus.IN_PROGRESS

    def can_be_edited_by(self, user_id: int) -> bool:
        return self.creator_id == user_id

    def add_assignee(self, user: "User") -> None:
        if user not in self.assignees:
            self.assignees.append(user)

    def remove_assignee(self, user: "User") -> None:
        if user in self.assignees:
            self.assignees.remove(user)

    def add_attachment(self, attachment: "Attachment") -> None:
        if attachment not in self.attachments:
            self.attachments.append(attachment)

    def remove_attachment(self, attachment: "Attachment") -> None:
        if attachment in self.attachments:
            self.attachments.remove(attachment)

    def add_tag(self, tag: "Tag") -> None:
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: "Tag") -> None:
        if tag in self.tags:
            self.tags.remove(tag)
# domain/task.py
from enum import Enum
from typing import Optional

class TaskStatus(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Task:
    def __init__(
        self,
        id: int,
        title: str,
        description: Optional[str],
        status: TaskStatus,
        creator_id: int,
        assignee_id: Optional[int] = None
    ):
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.creator_id = creator_id
        self.assignee_id = assignee_id

    def start_work(self, user_id: int):
        if user_id not in (self.creator_id, self.assignee_id):
            raise UnauthorizedTaskEditError()
        self.status = TaskStatus.IN_PROGRESS
from typing import Optional
from datetime import datetime
from domain.task import Task

class TimeLog:
    def __init__(
        self,
        id: int,
        task_id: int,
        user_id: int,
        duration_seconds: int,
        comment: Optional[str],
        logged_at: datetime
    ):
        self.id = id
        self.task_id = task_id
        self.user_id = user_id
        self.duration_seconds = duration_seconds
        self.comment = comment
        self.logged_at = logged_at

    def __repr__(self):
        return f"TimeLog(id={self.id}, task_id={self.task_id}, user_id={self.user_id}, duration_seconds={self.duration_seconds}, comment={self.comment}, logged_at={self.logged_at})"

    def __str__(self):
        return f"TimeLog(id={self.id}, task_id={self.task_id}, user_id={self.user_id}, duration_seconds={self.duration_seconds}, comment={self.comment}, logged_at={self.logged_at})"
from abc import ABC, abstractmethod
from typing import Optional, List

from domain.models.task import Task

class TaskRepository(ABC):
    @abstractmethod
    def create(self, task: Task) -> Task:
        pass

    @abstractmethod
    def delete(self, task_id: int) -> None:
        pass

    @abstractmethod
    def update(self, task: Task) -> Task:
        pass

    @abstractmethod
    def get_all(self) -> List[Task]:
        pass

    @abstractmethod
    def get_by_id(self, task_id: int) -> Optional[Task]:
        pass

    @abstractmethod
    def get_by_creator_id(self, creator_id: int) -> List[Task]:
        pass

    @abstractmethod
    def assign_task_to_user(self, task_id: int, user_id: int) -> None:
        pass

    @abstractmethod
    def unassign_task_from_user(self, task_id: int, user_id: int) -> None:
        pass

    @abstractmethod
    def get_all_assigned_to_user(self, user_id: int) -> List[Task]:
        pass

    @abstractmethod
    def get_all_with_tag(self, tag_id: int) -> List[Task]:
        pass

    @abstractmethod
    def get_all_with_attachment(self, attachment_id: int) -> List[Task]:
        pass

    @abstractmethod
    def change_status(self, task_id: int, status_id: int) -> None:
        pass

    @abstractmethod
    def add_comment(self, task_id: int, comment: str) -> None:
        pass

    @abstractmethod
    def add_attachment(self, task_id: int, attachment_id: int) -> None:
        pass

    @abstractmethod
    def remove_attachment(self, task_id: int, attachment_id: int) -> None:
        pass

    @abstractmethod
    def add_tag(self, task_id: int, tag_id: int) -> None:
        pass

    @abstractmethod
    def remove_tag(self, task_id: int, tag_id: int) -> None:
        pass

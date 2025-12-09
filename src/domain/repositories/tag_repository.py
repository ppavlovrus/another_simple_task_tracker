from abc import ABC, abstractmethod
from typing import Optional, List

from database.models import Tag
from domain.models.task import Task

class TagRepository(ABC):
    @abstractmethod
    def create(self, tag: Tag) -> Tag:
        pass

    @abstractmethod
    def delete(self, tag_id: int) -> None:
        pass

    @abstractmethod
    def get_all(self) -> List[Tag]:
        pass

    @abstractmethod
    def get_by_id(self, tag_id: int) -> Optional[Tag]:
        pass
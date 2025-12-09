from abc import ABC, abstractmethod
from typing import Optional, List

from domain.models.attachment import Attachment

class AttachmentsRepository(ABC):
    @abstractmethod
    def create(self, attachment: Attachment) -> Attachment:
        pass

    @abstractmethod
    def delete(self, attachment_id: int) -> None:
        pass

    @abstractmethod
    def get_all(self) -> List[Attachment]:
        pass

    @abstractmethod
    def get_by_task_id(self, task_id: int) -> List[Attachment]:
        pass

    @abstractmethod
    def get_by_id(self, attachment_id: int) -> Optional[Attachment]:
        pass
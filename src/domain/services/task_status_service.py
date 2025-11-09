"""TaskStatusService domain service for task status validation."""

from domain.exceptions.task_exceptions import InvalidTaskStatusTransitionError
from domain.models.task import Task, TaskStatus


class TaskStatusService:
    """Domain Service for validating task status transitions.
    
    This service implements business rules for task status changes
    according to FR-1.1 (task statuses) and ensures valid transitions.
    """
    
    # Разрешенные переходы статусов
    ALLOWED_TRANSITIONS = {
        TaskStatus.CREATED: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
        TaskStatus.IN_PROGRESS: {TaskStatus.PAUSED, TaskStatus.COMPLETED, TaskStatus.CANCELLED},
        TaskStatus.PAUSED: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
        TaskStatus.COMPLETED: set(),  # Завершенная задача не может менять статус
        TaskStatus.CANCELLED: set(),  # Отмененная задача не может менять статус
    }
    
    @classmethod
    def can_transition(cls, current: TaskStatus, target: TaskStatus) -> bool:
        """Проверяет, возможен ли переход между статусами.
        
        Args:
            current: Текущий статус
            target: Целевой статус
            
        Returns:
            True если переход разрешен
        """
        allowed = cls.ALLOWED_TRANSITIONS.get(current, set())
        return target in allowed
    
    @classmethod
    def validate_transition(
        cls, 
        task: Task, 
        new_status: TaskStatus
    ) -> None:
        """Валидирует переход статуса и выбрасывает исключение если невалидно.
        
        Args:
            task: Задача
            new_status: Новый статус
            
        Raises:
            InvalidTaskStatusTransitionError: Если переход не разрешен
        """
        if not cls.can_transition(task.status, new_status):
            raise InvalidTaskStatusTransitionError(
                current_status=task.status.value,
                target_status=new_status.value,
                task_id=task.id
            )
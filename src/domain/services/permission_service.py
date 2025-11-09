"""PermissionService domain service for access control validation."""

from domain.models.task import Task


class PermissionService:
    """Domain Service для проверки прав доступа к задачам."""
    
    @staticmethod
    def can_edit_task(user_id: int, task: Task, is_admin: bool = False) -> bool:
        """Проверяет, может ли пользователь редактировать задачу.
        
        Согласно FR-1.2 и FR-5.1:
        - Только creator, assignee или admin могут редактировать
        
        Args:
            user_id: ID пользователя
            task: Задача
            is_admin: Является ли пользователь администратором
            
        Returns:
            True если пользователь может редактировать
        """
        if is_admin:
            return True
        return user_id in (task.creator_id, task.assignee_id)
    
    @staticmethod
    def can_delete_task(user_id: int, task: Task, is_admin: bool = False) -> bool:
        """Проверяет, может ли пользователь удалять задачу.
        
        Согласно FR-5.2:
        - Только creator или admin могут удалять
        
        Args:
            user_id: ID пользователя
            task: Задача
            is_admin: Является ли пользователь администратором
            
        Returns:
            True если пользователь может удалять
        """
        if is_admin:
            return True
        return user_id == task.creator_id
    
    @staticmethod
    def can_change_assignee(user_id: int, task: Task, is_admin: bool = False) -> bool:
        """Проверяет, может ли пользователь менять исполнителя.
        
        Согласно FR-5.2:
        - Только creator или admin могут назначать исполнителя
        """
        if is_admin:
            return True
        return user_id == task.creator_id
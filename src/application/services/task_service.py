"""Task service for Application Layer.

This service orchestrates business logic for Task operations,
coordinates between repositories, and handles data transformation
between Pydantic schemas and domain models.
"""
import asyncpg
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status

from api.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from domain.models.task import Task
from domain.models.task_status import TaskStatus
from domain.repositories.task_repository import TaskRepository
from domain.repositories.task_repository_impl import TaskRepositoryImpl


class TaskService:
    """Service for managing Task operations.

    This service acts as a coordinator between the Presentation Layer (API)
    and the Domain/Infrastructure Layers. It handles:

    - Data transformation (Pydantic ↔ Domain models)
    - Business logic orchestration
    - Coordination between multiple repositories
    - Error handling and HTTP exception conversion
    - Transaction management (if needed)

    Args:
        db_conn: Database connection for repositories
        task_repo: Task repository instance (optional, created if not provided)
        user_repo: User repository instance (optional, for validation)
    """

    def __init__(
        self,
        db_conn: asyncpg.Connection,
        task_repo: Optional[TaskRepository] = None,
        user_repo: Optional[object] = None,  # UserRepository interface (optional)
    ):
        """Initialize TaskService with dependencies.

        Args:
            db_conn: Active database connection
            task_repo: Task repository (created if None)
            user_repo: User repository (optional, for user validation)
        """
        self.db_conn = db_conn
        self.task_repo = task_repo or TaskRepositoryImpl(db_conn)
        self.user_repo = user_repo  # Can be None if not needed

    async def create_task(self, task_data: TaskCreate, creator_id: Optional[int] = None) -> TaskResponse:
        """Create a new task.

        This method:
        1. Validates that creator exists (if user_repo provided)
        2. Sets default status to TO_DO if not provided
        3. Creates domain model from Pydantic schema
        4. Saves via repository
        5. Converts back to Pydantic response

        Args:
            task_data: Task creation data from API
            creator_id: Optional creator ID (overrides task_data.creator_id if provided)

        Returns:
            Created task as TaskResponse

        Raises:
            HTTPException: If validation fails or task creation fails
        """
        # Use provided creator_id or from task_data
        actual_creator_id = creator_id or task_data.creator_id

        # Validate creator exists (if user_repo available and has get_by_id method)
        if self.user_repo and hasattr(self.user_repo, "get_by_id"):
            creator = await self.user_repo.get_by_id(actual_creator_id)
            if not creator:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Creator with ID {actual_creator_id} not found",
                )

        # Set default status if not provided
        status_id = task_data.status_id or TaskStatus.TO_DO

        # Create domain model from Pydantic schema
        now = datetime.now()
        domain_task = Task(
            id=0,  # Will be set by database
            title=task_data.title,
            description=task_data.description,
            status_id=status_id,
            creator_id=actual_creator_id,
            deadline_start=task_data.deadline_start,
            deadline_end=task_data.deadline_end,
            created_at=now,
            updated_at=now,
        )

        try:
            # Save via repository
            created_task = await self.task_repo.create(domain_task)

            # Convert domain model to Pydantic response
            return self._domain_to_response(created_task)

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except asyncpg.ForeignKeyViolationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid foreign key reference: {e}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create task: {e}",
            )

    async def get_task_by_id(self, task_id: int) -> TaskResponse:
        """Get a task by its ID.

        Args:
            task_id: Task identifier

        Returns:
            Task as TaskResponse

        Raises:
            HTTPException: If task not found
        """
        task = await self.task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found",
            )

        return self._domain_to_response(task)

    async def get_all_tasks(self) -> List[TaskResponse]:
        """Get all tasks.

        Returns:
            List of tasks as TaskResponse
        """
        tasks = await self.task_repo.get_all()
        return [self._domain_to_response(task) for task in tasks]

    async def get_tasks_by_creator(self, creator_id: int) -> List[TaskResponse]:
        """Get all tasks created by a specific user.

        Args:
            creator_id: User identifier

        Returns:
            List of tasks as TaskResponse
        """
        tasks = await self.task_repo.get_by_creator_id(creator_id)
        return [self._domain_to_response(task) for task in tasks]

    async def update_task(
        self,
        task_id: int,
        task_data: TaskUpdate,
        user_id: Optional[int] = None,
    ) -> TaskResponse:
        """Update an existing task.

        This method:
        1. Loads existing task
        2. Validates user has permission to edit (if user_id provided)
        3. Applies partial updates
        4. Validates business rules (deadline_end >= deadline_start)
        5. Saves via repository

        Args:
            task_id: Task identifier
            task_data: Partial update data
            user_id: Optional user ID for permission check

        Returns:
            Updated task as TaskResponse

        Raises:
            HTTPException: If task not found, permission denied, or validation fails
        """
        # Load existing task
        existing_task = await self.task_repo.get_by_id(task_id)
        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found",
            )

        # Check permissions (if user_id provided)
        if user_id and not existing_task.can_be_edited_by(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this task",
            )

        # Apply partial updates
        updated_title = task_data.title if task_data.title is not None else existing_task.title
        updated_description = (
            task_data.description if task_data.description is not None else existing_task.description
        )
        updated_status_id = (
            task_data.status_id if task_data.status_id is not None else existing_task.status_id
        )
        updated_deadline_start = (
            task_data.deadline_start
            if task_data.deadline_start is not None
            else existing_task.deadline_start
        )
        updated_deadline_end = (
            task_data.deadline_end
            if task_data.deadline_end is not None
            else existing_task.deadline_end
        )

        # Create updated domain model
        updated_task = Task(
            id=existing_task.id,
            title=updated_title,
            description=updated_description,
            status_id=updated_status_id,
            creator_id=existing_task.creator_id,  # Creator cannot be changed
            deadline_start=updated_deadline_start,
            deadline_end=updated_deadline_end,
            created_at=existing_task.created_at,
            updated_at=datetime.now(),
            assignees=existing_task.assignees,
            attachments=existing_task.attachments,
            tags=existing_task.tags,
        )

        # Domain model validation will check deadline_end >= deadline_start
        # This will raise ValueError if invalid

        try:
            saved_task = await self.task_repo.update(updated_task)
            return self._domain_to_response(saved_task)

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except asyncpg.ForeignKeyViolationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid foreign key reference: {e}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update task: {e}",
            )

    async def delete_task(self, task_id: int, user_id: Optional[int] = None) -> None:
        """Delete a task.

        Args:
            task_id: Task identifier
            user_id: Optional user ID for permission check

        Raises:
            HTTPException: If task not found or permission denied
        """
        # Check permissions if user_id provided
        if user_id:
            existing_task = await self.task_repo.get_by_id(task_id)
            if not existing_task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with ID {task_id} not found",
                )

            if not existing_task.can_be_edited_by(user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this task",
                )

        try:
            await self.task_repo.delete(task_id)

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete task: {e}",
            )

    async def change_task_status(
        self,
        task_id: int,
        new_status_id: int,
        user_id: Optional[int] = None,
    ) -> TaskResponse:
        """Change task status with business rule validation.

        This method validates business rules:
        - Task can only transition to valid statuses
        - User must have permission to change status

        Args:
            task_id: Task identifier
            new_status_id: New status identifier
            user_id: Optional user ID for permission check

        Returns:
            Updated task as TaskResponse

        Raises:
            HTTPException: If task not found, invalid status transition, or permission denied
        """
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found",
            )

        # Check permissions
        if user_id and not task.can_be_edited_by(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to change status of this task",
            )

        # Validate status transition (using domain model methods)
        if new_status_id == TaskStatus.DONE and not task.can_be_completed():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot complete task with status {task.status_id}",
            )

        if new_status_id == TaskStatus.CANCELLED and not task.can_be_cancelled():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel task with status {task.status_id}",
            )

        if new_status_id == TaskStatus.IN_PROGRESS and not task.can_be_in_progress():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot set task to IN_PROGRESS from status {task.status_id}",
            )

        try:
            await self.task_repo.change_status(task_id, new_status_id)
            # Reload task to get updated data
            updated_task = await self.task_repo.get_by_id(task_id)
            return self._domain_to_response(updated_task)

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to change task status: {e}",
            )

    async def assign_task_to_user(self, task_id: int, user_id: int) -> None:
        """Assign a task to a user.

        Args:
            task_id: Task identifier
            user_id: User identifier

        Raises:
            HTTPException: If task or user not found
        """
        # Validate task exists
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found",
            )

        # Validate user exists (if user_repo available and has get_by_id method)
        if self.user_repo and hasattr(self.user_repo, "get_by_id"):
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User with ID {user_id} not found",
                )

        try:
            await self.task_repo.assign_task_to_user(task_id, user_id)

        except asyncpg.ForeignKeyViolationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid foreign key reference: {e}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to assign task: {e}",
            )

    async def unassign_task_from_user(self, task_id: int, user_id: int) -> None:
        """Unassign a task from a user.

        Args:
            task_id: Task identifier
            user_id: User identifier
        """
        try:
            await self.task_repo.unassign_task_from_user(task_id, user_id)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to unassign task: {e}",
            )

    async def get_tasks_assigned_to_user(self, user_id: int) -> List[TaskResponse]:
        """Get all tasks assigned to a user.

        Args:
            user_id: User identifier

        Returns:
            List of tasks as TaskResponse
        """
        tasks = await self.task_repo.get_all_assigned_to_user(user_id)
        return [self._domain_to_response(task) for task in tasks]

    def _domain_to_response(self, task: Task) -> TaskResponse:
        """Convert domain model to Pydantic response schema.

        This is a helper method for data transformation between layers.

        Args:
            task: Task domain model

        Returns:
            TaskResponse Pydantic schema
        """
        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status_id=task.status_id,
            creator_id=task.creator_id,
            deadline_start=task.deadline_start,
            deadline_end=task.deadline_end,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    async def add_attachment(self, task_id: int, attachment_id: int) -> None:
        """Add an attachment to a task.

        This method links an existing attachment to a task by updating
        the attachment's task_id field.

        Args:
            task_id: Task identifier
            attachment_id: Attachment identifier

        Raises:
            HTTPException: If task or attachment not found, or foreign key constraint violated
        """
        # Validate task exists
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found",
            )

        try:
            await self.task_repo.add_attachment(task_id, attachment_id)

        except ValueError as e:
            # Attachment not found (UPDATE 0)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except asyncpg.ForeignKeyViolationError as e:
            # Task doesn't exist (foreign key constraint)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid foreign key reference: {e}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add attachment: {e}",
            )



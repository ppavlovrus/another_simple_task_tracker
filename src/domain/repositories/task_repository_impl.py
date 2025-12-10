"""Implementation of TaskRepository using asyncpg.

This module provides the concrete implementation of TaskRepository
for PostgreSQL database using asyncpg driver.
"""
import asyncio
import asyncpg
from typing import List, Optional
from datetime import date, datetime

from domain.models.task import Task
from domain.models.user import User
from domain.models.tag import Tag
from domain.models.attachment import Attachment
from domain.repositories.task_repository import TaskRepository


class TaskRepositoryImpl(TaskRepository):
    """PostgreSQL implementation of TaskRepository using asyncpg.

    This repository maps database records to domain models and handles
    all database operations for Task entities.

    Args:
        db_conn: asyncpg database connection (should be provided via dependency injection)
    """

    def __init__(self, db_conn: asyncpg.Connection):
        """Initialize repository with database connection.

        Args:
            db_conn: Active asyncpg connection (managed by connection pool)
        """
        self.db_conn = db_conn

    def _row_to_task(self, row: asyncpg.Record) -> Task:
        """Convert database row to Task domain model.

        This is a helper method to map asyncpg.Record to Task domain model.
        It handles type conversions and default values.

        Args:
            row: Database record from asyncpg

        Returns:
            Task domain model instance
        """
        return Task(
            id=row["id"],
            title=row["title"],
            status_id=row["status_id"],
            creator_id=row["creator_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            description=row.get("description"),  # Optional field
            deadline_start=row.get("deadline_start"),  # Optional field
            deadline_end=row.get("deadline_end"),  # Optional field
            # Collections are loaded separately via _load_related_entities
            assignees=[],
            attachments=[],
            tags=[],
        )

    async def _load_assignees(self, task_id: int) -> List[User]:
        """Load assignees for a task.

        Args:
            task_id: Task identifier

        Returns:
            List of User domain models assigned to the task
        """
        rows = await self.db_conn.fetch(
            """
            SELECT u.id, u.username, u.email, u.password_hash, u.created_at, u.last_login
            FROM "user" u
            INNER JOIN task_assignee ta ON u.id = ta.user_id
            WHERE ta.task_id = $1
            ORDER BY ta.assigned_at
            """,
            task_id,
        )
        return [
            User(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                password_hash=row["password_hash"],
                created_at=row["created_at"],
                last_login=row.get("last_login"),
            )
            for row in rows
        ]

    async def _load_tags(self, task_id: int) -> List[Tag]:
        """Load tags for a task.

        Args:
            task_id: Task identifier

        Returns:
            List of Tag domain models associated with the task
        """
        rows = await self.db_conn.fetch(
            """
            SELECT t.id, t.name, t.created_at, t.updated_at
            FROM tag t
            INNER JOIN task_tag tt ON t.id = tt.tag_id
            WHERE tt.task_id = $1
            ORDER BY t.name
            """,
            task_id,
        )
        return [
            Tag(
                id=row["id"],
                name=row["name"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    async def _load_attachments(self, task_id: int) -> List[Attachment]:
        """Load attachments for a task.

        Args:
            task_id: Task identifier

        Returns:
            List of Attachment domain models for the task
        """
        rows = await self.db_conn.fetch(
            """
            SELECT id, task_id, filename, content_type, storage_path, size_bytes, uploaded_at
            FROM attachment
            WHERE task_id = $1
            ORDER BY uploaded_at
            """,
            task_id,
        )
        return [
            Attachment(
                id=row["id"],
                task_id=row["task_id"],
                filename=row["filename"],
                storage_path=row["storage_path"],
                uploaded_at=row["uploaded_at"],
                content_type=row.get("content_type"),
                size_bytes=row.get("size_bytes"),
            )
            for row in rows
        ]

    async def _load_related_entities(self, task: Task) -> Task:
        """Load all related entities (assignees, tags, attachments) for a task.

        This method populates the collections in the Task domain model.
        It's called after loading the main task data.

        Args:
            task: Task domain model (without collections)

        Returns:
            Task domain model with populated collections
        """
        # Load all related entities in parallel for better performance
        assignees, tags, attachments = await asyncio.gather(
            self._load_assignees(task.id),
            self._load_tags(task.id),
            self._load_attachments(task.id),
        )
        task.assignees = assignees
        task.tags = tags
        task.attachments = attachments
        return task

    async def create(self, task: Task) -> Task:
        """Create a new task in the database.

        Args:
            task: Task domain model to create (id should be None or 0)

        Returns:
            Created Task domain model with generated ID

        Raises:
            ValueError: If task creation fails
            asyncpg.ForeignKeyViolationError: If foreign key constraint violated
        """
        row = await self.db_conn.fetchrow(
            """
            INSERT INTO task (title, description, status_id, creator_id, deadline_start, deadline_end)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, title, description, status_id, creator_id, deadline_start, deadline_end, created_at, updated_at
            """,
            task.title,
            task.description,
            task.status_id,
            task.creator_id,
            task.deadline_start,
            task.deadline_end,
        )

        if not row:
            raise ValueError("Failed to create task")

        created_task = self._row_to_task(row)

        # If task has assignees, tags, or attachments, add them
        # Note: For new tasks, collections are usually empty, but we handle it anyway
        if task.assignees or task.tags or task.attachments:
            # Add assignees
            for user in task.assignees:
                await self.assign_task_to_user(created_task.id, user.id)

            # Add tags
            for tag in task.tags:
                await self.add_tag(created_task.id, tag.id)

            # Note: Attachments are usually created separately via AttachmentRepository
            # but if they're provided, we could add them here

        return created_task

    async def delete(self, task_id: int) -> None:
        """Delete a task from the database.

        Args:
            task_id: Task identifier

        Raises:
            ValueError: If task not found
        """
        result = await self.db_conn.execute(
            "DELETE FROM task WHERE id = $1",
            task_id,
        )
        # result is a string like "DELETE 1" or "DELETE 0"
        if result == "DELETE 0":
            raise ValueError(f"Task with ID {task_id} not found")

    async def update(self, task: Task) -> Task:
        """Update an existing task in the database.

        Args:
            task: Task domain model with updated data

        Returns:
            Updated Task domain model

        Raises:
            ValueError: If task not found
        """
        row = await self.db_conn.fetchrow(
            """
            UPDATE task
            SET title = $1,
                description = $2,
                status_id = $3,
                deadline_start = $4,
                deadline_end = $5,
                updated_at = NOW()
            WHERE id = $6
            RETURNING id, title, description, status_id, creator_id, deadline_start, deadline_end, created_at, updated_at
            """,
            task.title,
            task.description,
            task.status_id,
            task.deadline_start,
            task.deadline_end,
            task.id,
        )

        if not row:
            raise ValueError(f"Task with ID {task.id} not found")

        updated_task = self._row_to_task(row)
        # Reload related entities
        return await self._load_related_entities(updated_task)

    async def get_all(self) -> List[Task]:
        """Get all tasks from the database.

        Returns:
            List of all Task domain models
        """
        rows = await self.db_conn.fetch(
            """
            SELECT id, title, description, status_id, creator_id, deadline_start, deadline_end, created_at, updated_at
            FROM task
            ORDER BY created_at DESC
            """
        )

        tasks = [self._row_to_task(row) for row in rows]

        # Load related entities for all tasks
        # Note: This could be optimized with batch loading, but for simplicity we load individually
        for task in tasks:
            await self._load_related_entities(task)

        return tasks

    async def get_by_id(self, task_id: int) -> Optional[Task]:
        """Get a task by its ID.

        Args:
            task_id: Task identifier

        Returns:
            Task domain model if found, None otherwise
        """
        row = await self.db_conn.fetchrow(
            """
            SELECT id, title, description, status_id, creator_id, deadline_start, deadline_end, created_at, updated_at
            FROM task
            WHERE id = $1
            """,
            task_id,
        )

        if not row:
            return None

        task = self._row_to_task(row)
        return await self._load_related_entities(task)

    async def get_by_creator_id(self, creator_id: int) -> List[Task]:
        """Get all tasks created by a specific user.

        Args:
            creator_id: User identifier

        Returns:
            List of Task domain models created by the user
        """
        rows = await self.db_conn.fetch(
            """
            SELECT id, title, description, status_id, creator_id, deadline_start, deadline_end, created_at, updated_at
            FROM task
            WHERE creator_id = $1
            ORDER BY created_at DESC
            """,
            creator_id,
        )

        tasks = [self._row_to_task(row) for row in rows]

        # Load related entities
        for task in tasks:
            await self._load_related_entities(task)

        return tasks

    async def assign_task_to_user(self, task_id: int, user_id: int) -> None:
        """Assign a task to a user.

        Args:
            task_id: Task identifier
            user_id: User identifier

        Raises:
            asyncpg.UniqueViolationError: If assignment already exists
            asyncpg.ForeignKeyViolationError: If task or user not found
        """
        await self.db_conn.execute(
            """
            INSERT INTO task_assignee (task_id, user_id)
            VALUES ($1, $2)
            ON CONFLICT (task_id, user_id) DO NOTHING
            """,
            task_id,
            user_id,
        )

    async def unassign_task_from_user(self, task_id: int, user_id: int) -> None:
        """Unassign a task from a user.

        Args:
            task_id: Task identifier
            user_id: User identifier
        """
        await self.db_conn.execute(
            """
            DELETE FROM task_assignee
            WHERE task_id = $1 AND user_id = $2
            """,
            task_id,
            user_id,
        )

    async def get_all_assigned_to_user(self, user_id: int) -> List[Task]:
        """Get all tasks assigned to a specific user.

        Args:
            user_id: User identifier

        Returns:
            List of Task domain models assigned to the user
        """
        rows = await self.db_conn.fetch(
            """
            SELECT t.id, t.title, t.description, t.status_id, t.creator_id, t.deadline_start, t.deadline_end, t.created_at, t.updated_at
            FROM task t
            INNER JOIN task_assignee ta ON t.id = ta.task_id
            WHERE ta.user_id = $1
            ORDER BY t.created_at DESC
            """,
            user_id,
        )

        tasks = [self._row_to_task(row) for row in rows]

        # Load related entities
        for task in tasks:
            await self._load_related_entities(task)

        return tasks

    async def get_all_with_tag(self, tag_id: int) -> List[Task]:
        """Get all tasks with a specific tag.

        Args:
            tag_id: Tag identifier

        Returns:
            List of Task domain models with the tag
        """
        rows = await self.db_conn.fetch(
            """
            SELECT t.id, t.title, t.description, t.status_id, t.creator_id, t.deadline_start, t.deadline_end, t.created_at, t.updated_at
            FROM task t
            INNER JOIN task_tag tt ON t.id = tt.task_id
            WHERE tt.tag_id = $1
            ORDER BY t.created_at DESC
            """,
            tag_id,
        )

        tasks = [self._row_to_task(row) for row in rows]

        # Load related entities
        for task in tasks:
            await self._load_related_entities(task)

        return tasks

    async def get_all_with_attachment(self, attachment_id: int) -> List[Task]:
        """Get all tasks with a specific attachment.

        Args:
            attachment_id: Attachment identifier

        Returns:
            List of Task domain models with the attachment
        """
        rows = await self.db_conn.fetch(
            """
            SELECT t.id, t.title, t.description, t.status_id, t.creator_id, t.deadline_start, t.deadline_end, t.created_at, t.updated_at
            FROM task t
            INNER JOIN attachment a ON t.id = a.task_id
            WHERE a.id = $1
            ORDER BY t.created_at DESC
            """,
            attachment_id,
        )

        tasks = [self._row_to_task(row) for row in rows]

        # Load related entities
        for task in tasks:
            await self._load_related_entities(task)

        return tasks

    async def change_status(self, task_id: int, status_id: int) -> None:
        """Change the status of a task.

        Args:
            task_id: Task identifier
            status_id: New status identifier

        Raises:
            ValueError: If task not found
            asyncpg.ForeignKeyViolationError: If status_id is invalid
        """
        result = await self.db_conn.execute(
            """
            UPDATE task
            SET status_id = $1, updated_at = NOW()
            WHERE id = $2
            """,
            status_id,
            task_id,
        )

        if result == "UPDATE 0":
            raise ValueError(f"Task with ID {task_id} not found")

    async def add_comment(self, task_id: int, comment: str) -> None:
        """Add a comment to a task.

        Note: This method should probably be moved to CommentRepository
        according to DDD principles, but it's kept here for interface compatibility.

        Args:
            task_id: Task identifier
            comment: Comment content (should be a Comment domain model, but interface uses string)

        Raises:
            ValueError: If task not found
        """
        # This is a placeholder - in real implementation, you'd use CommentRepository
        # But for interface compatibility, we implement it here
        raise NotImplementedError(
            "add_comment should be implemented via CommentRepository. "
            "This method is kept for interface compatibility only."
        )

    async def add_attachment(self, task_id: int, attachment_id: int) -> None:
        """Add an attachment to a task.

        Note: Attachments are usually managed via AttachmentRepository.
        This method is for linking existing attachments to tasks.

        Args:
            task_id: Task identifier
            attachment_id: Attachment identifier

        Raises:
            ValueError: If task or attachment not found
        """
        # Verify that attachment belongs to this task (or update it)
        result = await self.db_conn.execute(
            """
            UPDATE attachment
            SET task_id = $1
            WHERE id = $2
            """,
            task_id,
            attachment_id,
        )

        if result == "UPDATE 0":
            raise ValueError(f"Attachment with ID {attachment_id} not found")

    async def remove_attachment(self, task_id: int, attachment_id: int) -> None:
        """Remove an attachment from a task.

        Note: This typically deletes the attachment, not just unlinks it.

        Args:
            task_id: Task identifier
            attachment_id: Attachment identifier
        """
        result = await self.db_conn.execute(
            """
            DELETE FROM attachment
            WHERE id = $1 AND task_id = $2
            """,
            attachment_id,
            task_id,
        )

        if result == "DELETE 0":
            raise ValueError(
                f"Attachment with ID {attachment_id} not found for task {task_id}"
            )

    async def add_tag(self, task_id: int, tag_id: int) -> None:
        """Add a tag to a task.

        Args:
            task_id: Task identifier
            tag_id: Tag identifier

        Raises:
            asyncpg.ForeignKeyViolationError: If task or tag not found
        """
        await self.db_conn.execute(
            """
            INSERT INTO task_tag (task_id, tag_id)
            VALUES ($1, $2)
            ON CONFLICT (task_id, tag_id) DO NOTHING
            """,
            task_id,
            tag_id,
        )

    async def remove_tag(self, task_id: int, tag_id: int) -> None:
        """Remove a tag from a task.

        Args:
            task_id: Task identifier
            tag_id: Tag identifier
        """
        await self.db_conn.execute(
            """
            DELETE FROM task_tag
            WHERE task_id = $1 AND tag_id = $2
            """,
            task_id,
            tag_id,
        )

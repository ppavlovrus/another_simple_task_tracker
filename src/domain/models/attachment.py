"""Attachment model for task file attachments.

This module contains the Attachment model for implementing
file attachment functionality (FR-4.1, FR-4.2, FR-4.3).
"""

from datetime import datetime


class Attachment:
    """Represents a file attachment to a task.

    According to FR-4.1, FR-4.2, FR-4.3:
    - Users can attach files to tasks (max N files, e.g., 10)
    - Supported formats: .pdf, .txt, .docx, .png, .jpg, .jpeg
    - Files are stored on disk or in object storage
    - Only metadata is stored in database: filename, content_type, size_bytes, storage_path, task_id

    Attributes:
        id: Unique identifier for the attachment
        task_id: ID of the task this attachment belongs to
        user_id: ID of the user who uploaded the file
        filename: Original filename
        content_type: MIME type of the file (e.g., "application/pdf", "image/png")
        size_bytes: File size in bytes
        storage_path: Path to the file in storage (disk or object storage)
        created_at: Timestamp when file was uploaded
    """

    def __init__(
        self,
        id: int,
        task_id: int,
        user_id: int,
        filename: str,
        content_type: str,
        size_bytes: int,
        storage_path: str,
        created_at: datetime,
    ) -> None:
        """Initialize Attachment instance.

        Args:
            id: Unique identifier for the attachment
            task_id: ID of the task this attachment belongs to
            user_id: ID of the user who uploaded the file
            filename: Original filename
            content_type: MIME type of the file (e.g., "application/pdf")
            size_bytes: File size in bytes
            storage_path: Path to the file in storage
            created_at: Timestamp when file was uploaded
        """
        self.id = id
        self.task_id = task_id
        self.user_id = user_id
        self.filename = filename
        self.content_type = content_type
        self.size_bytes = size_bytes
        self.storage_path = storage_path
        self.created_at = created_at

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"Attachment(id={self.id}, task_id={self.task_id}, "
            f"user_id={self.user_id}, filename={self.filename!r}, "
            f"content_type={self.content_type}, size_bytes={self.size_bytes}, "
            f"storage_path={self.storage_path!r}, created_at={self.created_at})"
        )

    def __str__(self) -> str:
        """Return human-readable string representation."""
        return (
            f"Attachment(id={self.id}, task_id={self.task_id}, "
            f"filename={self.filename}, size_bytes={self.size_bytes}, "
            f"created_at={self.created_at})"
        )
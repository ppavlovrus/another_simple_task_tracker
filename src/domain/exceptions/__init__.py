"""Domain exceptions module.

This module contains all domain-specific exceptions used throughout
the application for business logic error handling.
"""

from domain.exceptions.base import DomainException
from domain.exceptions.task_exceptions import (
    InvalidTaskStatusTransitionError,
    TaskAlreadyArchivedError,
    TaskNotFoundError,
    TaskTitleTooLongError,
)
from domain.exceptions.permission_exceptions import (
    PermissionDeniedError,
    UnauthorizedAssigneeChangeError,
    UnauthorizedTaskDeletionError,
    UnauthorizedTaskEditError,
)
from domain.exceptions.file_exceptions import (
    FileSizeExceededError,
    FileValidationError,
    MaxAttachmentsExceededError,
    UnsupportedFileTypeError,
)
from domain.exceptions.validation_exceptions import (
    InvalidDurationError,
    InvalidEmailError,
    ValidationError,
)

__all__ = [
    # Base
    "DomainException",
    # Task exceptions
    "TaskNotFoundError",
    "TaskAlreadyArchivedError",
    "InvalidTaskStatusTransitionError",
    "TaskTitleTooLongError",
    # Permission exceptions
    "UnauthorizedTaskEditError",
    "PermissionDeniedError",
    "UnauthorizedTaskDeletionError",
    "UnauthorizedAssigneeChangeError",
    # File exceptions
    "FileValidationError",
    "UnsupportedFileTypeError",
    "FileSizeExceededError",
    "MaxAttachmentsExceededError",
    # Validation exceptions
    "ValidationError",
    "InvalidEmailError",
    "InvalidDurationError",
]


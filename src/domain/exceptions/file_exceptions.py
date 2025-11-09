"""File and attachment related domain exceptions."""

from .base import DomainException


class FileValidationError(DomainException):
    """Base exception for file validation errors.

    This is a general exception for file-related validation issues.
    More specific exceptions should be used when possible.
    """

    def __init__(self, message: str, filename: str | None = None) -> None:
        """Initialize file validation error.

        Args:
            message: Error message
            filename: Optional filename that failed validation
        """
        super().__init__(message, error_code="FILE_VALIDATION_ERROR")
        self.filename = filename


class UnsupportedFileTypeError(FileValidationError):
    """Raised when file type is not supported.

    According to FR-4.2, supported formats are:
    .pdf, .txt, .docx, .png, .jpg, .jpeg
    """

    def __init__(
        self,
        filename: str,
        file_extension: str | None = None,
        supported_types: list[str] | None = None,
    ) -> None:
        """Initialize unsupported file type error.

        Args:
            filename: Name of the file with unsupported type
            file_extension: Optional file extension
            supported_types: Optional list of supported file types
        """
        if supported_types:
            types_str = ", ".join(supported_types)
            message = (
                f"File '{filename}' has unsupported type. "
                f"Supported types: {types_str}"
            )
        elif file_extension:
            message = f"File '{filename}' has unsupported extension: {file_extension}"
        else:
            message = f"File '{filename}' has unsupported type"

        super().__init__(message, filename=filename)
        self.error_code = "UNSUPPORTED_FILE_TYPE"
        self.file_extension = file_extension
        self.supported_types = supported_types or []


class FileSizeExceededError(FileValidationError):
    """Raised when file size exceeds maximum allowed size.

    This exception is raised when a file is too large to be uploaded.
    """

    def __init__(
        self,
        filename: str,
        file_size: int,
        max_size: int,
        size_unit: str = "bytes",
    ) -> None:
        """Initialize file size exceeded error.

        Args:
            filename: Name of the file that is too large
            file_size: Actual file size
            max_size: Maximum allowed file size
            size_unit: Unit for size display (default: "bytes")
        """
        message = (
            f"File '{filename}' size ({file_size} {size_unit}) exceeds "
            f"maximum allowed size ({max_size} {size_unit})"
        )
        super().__init__(message, filename=filename)
        self.error_code = "FILE_SIZE_EXCEEDED"
        self.file_size = file_size
        self.max_size = max_size
        self.size_unit = size_unit


class MaxAttachmentsExceededError(DomainException):
    """Raised when task already has maximum number of attachments.

    According to FR-4.1, there is a maximum number of files
    per task (e.g., 10 files).
    """

    def __init__(
        self,
        task_id: int,
        current_count: int,
        max_count: int = 10,
    ) -> None:
        """Initialize max attachments exceeded error.

        Args:
            task_id: ID of the task
            current_count: Current number of attachments
            max_count: Maximum allowed attachments (default: 10)
        """
        message = (
            f"Task {task_id} already has {current_count} attachments. "
            f"Maximum allowed: {max_count}"
        )
        super().__init__(message, error_code="MAX_ATTACHMENTS_EXCEEDED")
        self.task_id = task_id
        self.current_count = current_count
        self.max_count = max_count


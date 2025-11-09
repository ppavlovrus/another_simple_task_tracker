"""FileValidationService domain service for file validation."""

import os

from domain.exceptions.file_exceptions import (
    FileSizeExceededError,
    UnsupportedFileTypeError,
)


class FileValidationService:
    """Domain Service for file validation.
    
    This service validates files according to FR-4.2 and NFR-2.6:
    - Validates file extensions
    - Validates MIME types
    - Validates file sizes
    """
    
    # Поддерживаемые MIME-типы согласно FR-4.2
    ALLOWED_MIME_TYPES = {
        "application/pdf",  # .pdf
        "text/plain",  # .txt
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "image/png",  # .png
        "image/jpeg",  # .jpg, .jpeg
    }
    
    ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".png", ".jpg", ".jpeg"}
    
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
    
    @classmethod
    def validate_file(
        cls,
        filename: str,
        content_type: str,
        size_bytes: int,
    ) -> None:
        """Валидирует файл согласно FR-4.2 и NFR-2.6.
        
        Args:
            filename: Имя файла
            content_type: MIME-тип файла
            size_bytes: Размер файла в байтах
            
        Raises:
            UnsupportedFileTypeError: Если тип файла не поддерживается
            FileSizeExceededError: Если размер файла превышает лимит
        """
        # Проверка расширения
        extension = os.path.splitext(filename)[1].lower()
        if extension not in cls.ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                filename=filename,
                file_extension=extension,
                supported_types=list(cls.ALLOWED_EXTENSIONS)
            )
        
        # Проверка MIME-типа
        if content_type not in cls.ALLOWED_MIME_TYPES:
            raise UnsupportedFileTypeError(
                filename=filename,
                supported_types=list(cls.ALLOWED_MIME_TYPES)
            )
        
        # Проверка размера
        if size_bytes > cls.MAX_FILE_SIZE_BYTES:
            raise FileSizeExceededError(
                filename=filename,
                file_size=size_bytes,
                max_size=cls.MAX_FILE_SIZE_BYTES
            )
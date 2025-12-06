print(">>> START attachment.py")
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

print(">>> IMPORTS done")

@dataclass
class Attachment:
    id: int
    task_id: int
    filename: str
    storage_path: str
    uploaded_at: datetime

    content_type: Optional[str] = None
    size_bytes: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate attachment data after initialization."""
        if not self.filename or not self.filename.strip():
           raise ValueError("Attachment filename cannot be empty or whitespace only")
       
        if not self.storage_path or not self.storage_path.strip():
            raise ValueError("Attachment storage path cannot be empty or whitespace only")
        
        if self.size_bytes and self.size_bytes < 0:
            raise ValueError("Attachment size bytes cannot be negative")

    def get_url(self) -> str:
        return f"{self.storage_path}/{self.filename}"

print(">>> Attachment class defined")
print(">>> NAMES in module:", list(globals().keys()))
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from pydantic import StringConstraints

FilenameStr = Annotated[
    str,
    StringConstraints(min_length=1, max_length=255, strip_whitespace=True),
]

ContentTypeStr = Annotated[
    str,
    StringConstraints(min_length=1, max_length=100, strip_whitespace=True),
]

StoragePathStr = Annotated[
    str,
    StringConstraints(min_length=1, strip_whitespace=True),
]

# Positive file size constraint
NonNegativeInt = Annotated[int, Field(ge=0)]


class AttachmentCreate(BaseModel):
    """Request model: create attachment."""
    task_id: int
    filename: FilenameStr
    storage_path: StoragePathStr
    content_type: Optional[ContentTypeStr] = None
    size_bytes: Optional[NonNegativeInt] = None

class AttachmentResponse(BaseModel):
    """Response model: attachment data."""
    id: int
    task_id: int
    filename: str
    content_type: Optional[str] = None
    storage_path: str
    size_bytes: Optional[int] = None
    uploaded_at: datetime


class AttachmentUpdate(BaseModel):
    """Request model: attachment update."""
    filename: Optional[FilenameStr] = None
    content_type: Optional[ContentTypeStr] = None
    storage_path: Optional[StoragePathStr] = None
    size_bytes: Optional[NonNegativeInt] = None

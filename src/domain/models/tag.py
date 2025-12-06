from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Tag:
    """Tag domain model.
    
    Note: In DDD, we don't store reverse relationships (like tasks) 
    in domain models to avoid circular dependencies and maintain encapsulation.
    """
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Validate tag data after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Tag name cannot be empty or whitespace only")
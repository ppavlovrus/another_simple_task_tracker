from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User domain model.
    
    Note: In DDD, we don't store reverse relationships (like tasks) 
    in domain models to avoid circular dependencies and maintain encapsulation.
    """
    id: int
    username: str
    email: str
    password_hash: str  # Never store plain password in domain model
    created_at: datetime
    last_login: Optional[datetime] = None
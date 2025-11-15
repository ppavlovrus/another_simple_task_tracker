"""Application configuration."""
import os
from typing import Optional

# Database configuration
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost/task_tracker"
)

# Connection pool settings
DB_POOL_MIN_SIZE: int = int(os.getenv("DB_POOL_MIN_SIZE", "10"))
DB_POOL_MAX_SIZE: int = int(os.getenv("DB_POOL_MAX_SIZE", "20"))
DB_POOL_COMMAND_TIMEOUT: int = int(os.getenv("DB_POOL_COMMAND_TIMEOUT", "60"))
DB_POOL_MAX_QUERIES: int = int(os.getenv("DB_POOL_MAX_QUERIES", "50000"))
DB_POOL_MAX_INACTIVE_LIFETIME: float = float(
    os.getenv("DB_POOL_MAX_INACTIVE_LIFETIME", "300.0")
)


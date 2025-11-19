"""Application configuration."""
import os
from typing import Optional
from urllib.parse import quote

# Database configuration
DATABASE_NAME: str = os.getenv("DATABASE_NAME", "task_tracker")
DATABASE_USER: str = os.getenv("DATABASE_USER", "postgres")
DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "")
DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT: str = os.getenv("DATABASE_PORT", "5432")
_ENV_DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
if _ENV_DATABASE_URL:
    DATABASE_URL: str = _ENV_DATABASE_URL
else:
    user_enc = quote(DATABASE_USER, safe="")
    if DATABASE_PASSWORD:
        password_enc = quote(DATABASE_PASSWORD, safe="")
        auth_part = f"{user_enc}:{password_enc}@"
    else:
        auth_part = f"{user_enc}@"
    DATABASE_URL: str = f"postgresql://{auth_part}{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

# Connection pool settings
DB_POOL_MIN_SIZE: int = int(os.getenv("DB_POOL_MIN_SIZE", "10"))
DB_POOL_MAX_SIZE: int = int(os.getenv("DB_POOL_MAX_SIZE", "20"))
DB_POOL_COMMAND_TIMEOUT: int = int(os.getenv("DB_POOL_COMMAND_TIMEOUT", "60"))
DB_POOL_MAX_QUERIES: int = int(os.getenv("DB_POOL_MAX_QUERIES", "50000"))
DB_POOL_MAX_INACTIVE_LIFETIME: float = float(
    os.getenv("DB_POOL_MAX_INACTIVE_LIFETIME", "300.0")
)


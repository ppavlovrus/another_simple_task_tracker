# Рефакторинг структуры проекта: Разбиение main.py

## Текущая проблема

Файл `main.py` содержит 718 строк и включает:
- Конфигурацию
- Pydantic модели (6 классов)
- Lifespan управление
- FastAPI app
- Dependencies
- Task endpoints (4 функции)
- User endpoints (4 функции)

**Проблемы:**
- Сложно поддерживать
- Сложно тестировать
- Нарушение Single Responsibility Principle
- Сложно масштабировать

---

## Предлагаемая структура

```
src/
├── main.py                    # Точка входа, создание app
├── config.py                  # Конфигурация приложения
├── database.py                # Управление connection pool
├── dependencies.py            # FastAPI dependencies
│
├── api/                       # API слой
│   ├── __init__.py
│   ├── routers/              # API роутеры
│   │   ├── __init__.py
│   │   ├── tasks.py          # Task endpoints
│   │   └── users.py          # User endpoints
│   │
│   └── schemas/              # Pydantic модели
│       ├── __init__.py
│       ├── task.py           # Task schemas
│       └── user.py           # User schemas
│
└── core/                      # Ядро приложения (опционально)
    ├── __init__.py
    └── exceptions.py         # Обработка ошибок
```

---

## Детальная структура

### 1. `config.py` - Конфигурация

```python
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
```

**Что выносим:**
- `DATABASE_URL`
- Настройки connection pool
- Другие конфигурационные параметры

---

### 2. `database.py` - Управление БД

```python
"""Database connection pool management."""
import asyncpg
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI

from config import (
    DATABASE_URL,
    DB_POOL_MIN_SIZE,
    DB_POOL_MAX_SIZE,
    DB_POOL_COMMAND_TIMEOUT,
)

# Global connection pool
db_pool: Optional[asyncpg.Pool] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database connection pool lifecycle."""
    global db_pool

    # Startup: create connection pool
    db_pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=DB_POOL_MIN_SIZE,
        max_size=DB_POOL_MAX_SIZE,
        command_timeout=DB_POOL_COMMAND_TIMEOUT,
        max_queries=50000,
        max_inactive_connection_lifetime=300.0,
    )
    print("Database connection pool created")

    yield

    # Shutdown: close connection pool
    await db_pool.close()
    print("Database connection pool closed")


def get_pool() -> Optional[asyncpg.Pool]:
    """Get database connection pool."""
    return db_pool
```

**Что выносим:**
- `db_pool` глобальная переменная
- `lifespan` функция
- Функция для получения пула

---

### 3. `dependencies.py` - FastAPI Dependencies

```python
"""FastAPI dependencies."""
import asyncpg
from fastapi import Depends, HTTPException, status
from typing import Annotated

from application.services import get_pool


async def get_db_connection() -> asyncpg.Connection:
    """Get database connection from pool.

    This dependency provides a connection from the connection pool.
    The connection is automatically returned to the pool after use.

    Yields:
        Database connection from pool

    Raises:
        HTTPException: If connection pool is not initialized
    """
    pool = get_pool()
    if pool is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection pool not initialized",
        )

    async with pool.acquire() as connection:
        yield connection
```

**Что выносим:**
- `get_db_connection` dependency
- Другие dependencies (если появятся)

---

### 4. `api/schemas/task.py` - Task Pydantic модели

```python
"""Task Pydantic schemas."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class TaskCreate(BaseModel):
    """Request model for creating a new task."""

    title: str
    description: Optional[str] = None
    status_id: int
    creator_id: int
    assignee_id: Optional[int] = None
    deadline_start: Optional[date] = None
    deadline_end: Optional[date] = None


class TaskUpdate(BaseModel):
    """Request model for updating a task."""

    title: Optional[str] = None
    description: Optional[str] = None
    status_id: Optional[int] = None
    assignee_id: Optional[int] = None
    deadline_start: Optional[date] = None
    deadline_end: Optional[date] = None


class TaskResponse(BaseModel):
    """Response model for task data."""

    id: int
    title: str
    description: Optional[str]
    status_id: int
    creator_id: int
    assignee_id: Optional[int]
    deadline_start: Optional[date]
    deadline_end: Optional[date]
    created_at: datetime
    updated_at: datetime
```

**Что выносим:**
- Все Task-related Pydantic модели

---

### 5. `api/schemas/user.py` - User Pydantic модели

```python
"""User Pydantic schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    """Request model for creating a new user."""

    username: str
    email: str
    password: str


class UserUpdate(BaseModel):
    """Request model for updating a user."""

    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    """Response model for user data."""

    id: int
    username: str
    email: str
    created_at: datetime
    last_login: Optional[datetime] = None
```

**Что выносим:**
- Все User-related Pydantic модели

---

### 6. `api/routers/tasks.py` - Task endpoints

```python
"""Task API endpoints."""
import asyncpg
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from dependencies import get_db_connection

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="Create a new task with optional assignees and deadlines",
)
async def create_task(
    task: TaskCreate,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> TaskResponse:
    """Create a new task in the database."""
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO tasks (title, description, status_id, creator_id, assignee_id, deadline_start, deadline_end)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, title, description, status_id, creator_id, assignee_id, deadline_start, deadline_end, created_at, updated_at
            """,
            task.title,
            task.description,
            task.status_id,
            task.creator_id,
            task.assignee_id,
            task.deadline_start,
            task.deadline_end,
        )

        if not row:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create task",
            )

        return TaskResponse(**row)

    except asyncpg.ForeignKeyViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid foreign key reference: {e}",
        )
    except asyncpg.UniqueViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Unique constraint violation: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}",
        )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task by ID",
    description="Retrieve a task with its assignees by task ID",
)
async def get_task(
    task_id: int,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> TaskResponse:
    """Get task by ID from database."""
    row = await conn.fetchrow(
        """
        SELECT id, title, description, status_id, creator_id, assignee_id,
               deadline_start, deadline_end, created_at, updated_at
        FROM tasks
        WHERE id = $1
        """,
        task_id,
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )

    return TaskResponse(**row)


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task by ID",
    description="Update a task with its assignees by task ID",
)
async def update_task(
    task_id: int,
    task: TaskUpdate,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> TaskResponse:
    """Update task by ID in database."""
    # ... (динамическое обновление)
    pass


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task by ID",
    description="Delete a task by task ID",
)
async def delete_task(
    task_id: int,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> None:
    """Delete task by ID from database."""
    # ... (удаление)
    pass
```

**Что выносим:**
- Все Task endpoints
- Используем `APIRouter` вместо прямого `@app.post`

---

### 7. `api/routers/users.py` - User endpoints

```python
"""User API endpoints."""
import asyncpg
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas.user import UserCreate, UserResponse, UserUpdate
from dependencies import get_db_connection

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user with username, email, and password",
)
async def create_user(
    user: UserCreate,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> UserResponse:
    """Create a new user in the database."""
    # ... (создание пользователя)
    pass


# ... остальные endpoints (get, update, delete)
```

**Что выносим:**
- Все User endpoints
- Используем `APIRouter`

---

### 8. `main.py` - Точка входа (упрощенная)

```python
"""FastAPI application entry point."""
from fastapi import FastAPI

from api.routers import tasks, users
from application.services import lifespan

# FastAPI application initialization
app = FastAPI(
    title="Task Tracker API",
    description="REST API for task management system",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(tasks.router)
app.include_router(users.router)

# Application entry point
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

**Что остается:**
- Создание FastAPI app
- Подключение routers
- Entry point для запуска

---

## Преимущества новой структуры

### 1. Разделение ответственности

- **config.py** - только конфигурация
- **database.py** - только управление БД
- **dependencies.py** - только dependencies
- **api/schemas/** - только Pydantic модели
- **api/routers/** - только endpoints

### 2. Легче поддерживать

- Каждый файл отвечает за одну вещь
- Легко найти нужный код
- Легко добавлять новые endpoints

### 3. Легче тестировать

- Можно тестировать каждый модуль отдельно
- Можно мокать dependencies
- Можно тестировать routers изолированно

### 4. Масштабируемость

- Легко добавлять новые routers
- Легко добавлять новые schemas
- Легко добавлять новые dependencies

### 5. Переиспользование

- Schemas можно использовать в разных местах
- Dependencies можно использовать в разных routers
- Database pool доступен везде

---

## Сравнение: До и После

### До (main.py - 718 строк):

```python
# main.py
# - Конфигурация
# - Pydantic модели (6 классов)
# - Lifespan
# - FastAPI app
# - Dependencies
# - Task endpoints (4 функции)
# - User endpoints (4 функции)
# ВСЕ В ОДНОМ ФАЙЛЕ!
```

### После (разбито на модули):

```
src/
├── main.py              # ~20 строк - только создание app
├── config.py            # ~15 строк - конфигурация
├── database.py          # ~40 строк - управление БД
├── dependencies.py      # ~30 строк - dependencies
│
├── api/
│   ├── schemas/
│   │   ├── task.py      # ~50 строк - Task модели
│   │   └── user.py      # ~35 строк - User модели
│   │
│   └── routers/
│       ├── tasks.py     # ~200 строк - Task endpoints
│       └── users.py     # ~200 строк - User endpoints
```

**Итого:** ~590 строк, но разбито на логические модули!

---

## Пошаговый план рефакторинга

### Шаг 1: Создать структуру папок

```bash
mkdir -p src/api/schemas
mkdir -p src/api/routers
touch src/config.py
touch src/database.py
touch src/dependencies.py
touch src/api/__init__.py
touch src/api/schemas/__init__.py
touch src/api/routers/__init__.py
touch src/api/schemas/task.py
touch src/api/schemas/user.py
touch src/api/routers/tasks.py
touch src/api/routers/users.py
```

### Шаг 2: Вынести конфигурацию

- Создать `config.py`
- Перенести `DATABASE_URL` и настройки пула

### Шаг 3: Вынести database

- Создать `database.py`
- Перенести `db_pool` и `lifespan`

### Шаг 4: Вынести dependencies

- Создать `dependencies.py`
- Перенести `get_db_connection`

### Шаг 5: Вынести schemas

- Создать `api/schemas/task.py` и `api/schemas/user.py`
- Перенести Pydantic модели

### Шаг 6: Вынести routers

- Создать `api/routers/tasks.py` и `api/routers/users.py`
- Перенести endpoints, использовать `APIRouter`

### Шаг 7: Упростить main.py

- Оставить только создание app и подключение routers

### Шаг 8: Тестирование

- Проверить, что все работает
- Исправить импорты если нужно

---

## Альтернативная структура (более продвинутая)

Если проект будет расти, можно использовать более сложную структуру:

```
src/
├── main.py
├── config.py
├── database.py
├── dependencies.py
│
├── api/
│   ├── __init__.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── tasks.py
│   │   └── users.py
│   │
│   └── schemas/
│       ├── __init__.py
│       ├── task.py
│       └── user.py
│
├── services/              # Бизнес-логика (если появится)
│   ├── __init__.py
│   ├── task_service.py
│   └── user_service.py
│
└── repositories/         # Доступ к данным (если появится)
    ├── __init__.py
    ├── task_repository.py
    └── user_repository.py
```

Но для текущего проекта первая структура достаточна!

---

## Резюме

### Что делать:

1. ✅ Создать структуру папок
2. ✅ Вынести конфигурацию в `config.py`
3. ✅ Вынести database в `database.py`
4. ✅ Вынести dependencies в `dependencies.py`
5. ✅ Вынести schemas в `api/schemas/`
6. ✅ Вынести routers в `api/routers/`
7. ✅ Упростить `main.py`

### Преимущества:

- ✅ Разделение ответственности
- ✅ Легче поддерживать
- ✅ Легче тестировать
- ✅ Масштабируемость
- ✅ Переиспользование кода

### Результат:

- `main.py` уменьшится с 718 до ~20 строк
- Код разбит на логические модули
- Легко добавлять новые endpoints и модели

Это стандартная структура для FastAPI проектов! 🎯


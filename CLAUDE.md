# Project: Another Simple Task Tracker

## Project Description

REST API для управления задачами, создаваемый в учебных целях. Проект реализует систему трекинга задач с поддержкой пользователей, комментариев, файловых вложений, временных логов и уведомлений.

**Цель проекта:** Изучение и практика Domain-Driven Design (DDD), разработка REST API на FastAPI, работа с асинхронными операциями БД.

## Tech Stack

- **Web Framework:** FastAPI 0.121.2
- **Database Driver:** asyncpg 0.30.0 (асинхронный доступ к PostgreSQL)
- **ORM для миграций:** SQLAlchemy 2.0.44 (только для Alembic, не для runtime)
- **Validation:** Pydantic 2.12.4
- **Migrations:** Alembic
- **ASGI Server:** Uvicorn 0.38.0
- **Testing:** pytest
- **Database:** PostgreSQL

## Architecture

Проект следует принципам **Domain-Driven Design (DDD)** с разделением на слои:

```
Presentation Layer (FastAPI) → Application Layer → Domain Layer → Infrastructure Layer
```

**Текущее состояние:**
- ✅ Presentation Layer: FastAPI роутеры и Pydantic схемы
- ✅ Infrastructure Layer: asyncpg connection pooling
- ✅ Миграции: Alembic с SQLAlchemy моделями
- 🚧 Domain Layer: частично (интерфейсы определены)
- 🚧 Application Layer: в разработке
- 🚧 Repositories: интерфейсы есть, реализации отсутствуют

## Project Structure

```
src/
├── main.py                 # FastAPI app entry point
├── config.py              # Configuration (env vars)
├── dependencies.py        # FastAPI dependencies
│
├── api/                   # Presentation Layer
│   ├── routers/          # API endpoints
│   │   ├── tasks.py      # CRUD для задач
│   │   ├── users.py      # CRUD для пользователей
│   │   ├── tags.py       # CRUD для тегов
│   │   └── attachments.py # CRUD для вложений
│   └── schemas/          # Pydantic models
│       ├── task.py       # TaskCreate, TaskUpdate, TaskResponse
│       ├── user.py       # UserCreate, UserUpdate, UserResponse
│       ├── tags.py
│       └── attachment.py
│
├── database/             # Infrastructure Layer
│   ├── models.py        # SQLAlchemy models (для Alembic только)
│   └── pool.py          # Connection pool management
│
└── sql/
    └── database_creation.sql  # Исходная схема БД
```

## Code Style & Patterns

### 1. Async/Await Everywhere
- **Всегда** используйте `async/await` для операций с БД
- Все endpoint функции должны быть `async`
- Используйте `asyncpg` для всех запросов к БД

```python
@router.post("/", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
) -> TaskResponse:
    row = await conn.fetchrow("SELECT ...", ...)
```

### 2. Dependency Injection
- Используйте `Depends(get_db_connection)` для получения соединения из пула
- Используйте `Annotated[Type, Depends(...)]` для type hints
- НЕ создавайте соединения вручную

```python
from typing import Annotated
from fastapi import Depends
from dependencies import get_db_connection

async def my_endpoint(
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)],
):
    # conn автоматически из пула
```

### 3. Pydantic Schemas Pattern
Для каждого ресурса создавайте три схемы:

- **`*Create`** — все обязательные поля (без `Optional`)
- **`*Update`** — все поля `Optional` (для partial update)
- **`*Response`** — включает `id`, timestamps

```python
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status_id: int
    # ...

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    # Все Optional для partial update

class TaskResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    # ...
```

### 4. Partial Update Pattern
Для `*Update` endpoints:
- Проверяйте, что хотя бы одно поле не `None`
- Динамически стройте SQL запрос (только не-`None` поля)
- Всегда обновляйте `updated_at = NOW()`

```python
# Пример из update_task
update_fields = []
if task.title is not None:
    update_fields.append(f"title = ${param_index}")
    values.append(task.title)
    param_index += 1
# ...
update_fields.append("updated_at = NOW()")
query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ${param_index}"
```

### 5. Error Handling
- Используйте `HTTPException` из FastAPI
- Правильные HTTP статус коды:
  - `400` — Bad Request (валидация, foreign key violation)
  - `404` — Not Found
  - `409` — Conflict (unique constraint violation)
  - `500` — Internal Server Error
- Обрабатывайте `asyncpg` исключения:
  - `asyncpg.ForeignKeyViolationError` → 400
  - `asyncpg.UniqueViolationError` → 409

```python
try:
    row = await conn.fetchrow(...)
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
```

### 6. Type Hints
- **Всегда** используйте type hints
- Используйте `Annotated` для dependencies
- Используйте `Optional` для nullable полей

### 7. Database Connection
- **НЕ** создавайте соединения вручную
- Используйте `get_db_connection()` dependency
- Соединение автоматически возвращается в пул после запроса

### 8. SQL Queries
- Используйте параметризованные запросы (`$1`, `$2`, ...)
- **НЕ** используйте f-strings для значений (SQL injection risk)
- Используйте `fetchrow()` для одной строки, `fetch()` для нескольких

```python
# ✅ Правильно
row = await conn.fetchrow(
    "SELECT * FROM tasks WHERE id = $1",
    task_id,
)

# ❌ Неправильно
row = await conn.fetchrow(f"SELECT * FROM tasks WHERE id = {task_id}")
```

## Database

### Schema Naming
- Таблицы в **единственном числе**: `user`, `task`, `tag`, `attachment`
- Foreign keys с каскадным удалением где уместно

### Key Tables
- `user` — пользователи
- `task` — задачи
- `task_status` — справочник статусов
- `task_assignee` — связь задачи ↔ исполнители (many-to-many)
- `tag` — теги
- `task_tag` — связь задачи ↔ теги (many-to-many)
- `attachment` — файловые вложения
- `auth_session` — сессии аутентификации

### Migrations
- **Инструмент:** Alembic
- **Модели:** SQLAlchemy в `src/database/models.py` (только для миграций)
- **Runtime:** asyncpg (НЕ SQLAlchemy)
- **Автогенерация:** `alembic revision --autogenerate -m "description"`

## Configuration

### Environment Variables
```bash
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=pass
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=task_tracker
DATABASE_URL=postgresql://user:pass@host:port/dbname  # Можно задать напрямую

DB_POOL_MIN_SIZE=10
DB_POOL_MAX_SIZE=20
DB_POOL_COMMAND_TIMEOUT=60
```

### Connection Pool
- Создается в `lifespan` (startup)
- Закрывается при shutdown
- Глобальная переменная `db_pool` в `src/database/pool.py`
- Используется через `get_db_connection()` dependency

## Common Commands

```bash
# Запуск приложения
uvicorn src.main:app --reload

# Миграции
alembic upgrade head              # Применить миграции
alembic revision --autogenerate -m "description"  # Создать миграцию
alembic upgrade head --sql         # Просмотреть SQL (offline mode)

# Тесты
pytest                             # Запустить тесты
pytest --cov=src                   # С покрытием кода
```

## Important Notes

### ⚠️ Что НЕ использовать:
- ❌ SQLAlchemy для runtime операций (только для миграций)
- ❌ Синхронные драйверы БД (psycopg2)
- ❌ Создание соединений вручную (используйте dependency)
- ❌ f-strings для SQL значений (SQL injection risk)
- ❌ Flask или другие фреймворки (только FastAPI)

### ✅ Что использовать:
- ✅ asyncpg для всех БД операций
- ✅ FastAPI Depends для dependency injection
- ✅ Pydantic для валидации
- ✅ async/await везде
- ✅ Type hints везде
- ✅ Параметризованные SQL запросы

## Current API Endpoints

### Tasks (`/tasks`)
- `POST /tasks/` — создать задачу
- `GET /tasks/{task_id}` — получить задачу
- `PUT /tasks/{task_id}` — обновить задачу (partial update)
- `DELETE /tasks/{task_id}` — удалить задачу

### Users (`/users`)
- `POST /users/` — создать пользователя
- `GET /users/{user_id}` — получить пользователя
- `PUT /users/{user_id}` — обновить пользователя
- `DELETE /users/{user_id}` — удалить пользователя

### Tags (`/tags`)
- `POST /tags/` — создать тег
- `GET /tags/` — список всех тегов
- `DELETE /tags/{tag_id}` — удалить тег

### Attachments (`/attachments`)
- `POST /attachments/` — создать вложение
- `GET /attachments/{attachment_id}` — получить вложение
- `DELETE /attachments/{attachment_id}` — удалить вложение

## Known Issues & TODOs

### Critical
- [ ] Пароли хранятся в plain text (нужно добавить bcrypt/passlib)

### Important
- [ ] Нет аутентификации (JWT/сессии)
- [ ] Domain Layer не интегрирован в API
- [ ] Нет реализации Repositories
- [ ] Нет Comments API
- [ ] Нет Time Logs API

## Development Workflow

1. **Создание нового endpoint:**
   - Добавить Pydantic схемы в `src/api/schemas/`
   - Создать endpoint в соответствующем router
   - Использовать `async/await` и `Depends(get_db_connection)`
   - Обработать ошибки через `HTTPException`

2. **Добавление новой таблицы:**
   - Добавить SQLAlchemy модель в `src/database/models.py`
   - Создать миграцию: `alembic revision --autogenerate -m "add table"`
   - Применить: `alembic upgrade head`

3. **Тестирование:**
   - Писать тесты в `test/`
   - Использовать fixtures из `test/conftest.py`
   - Запускать через `pytest`

## Additional Context

Для более подробной информации см.:
- `.ai-context/project_context.md` — полный контекст проекта
- `docs/requirements.md` — функциональные требования
- `docs/user_stories.md` — пользовательские истории
- `alembic/README.md` — документация по миграциям






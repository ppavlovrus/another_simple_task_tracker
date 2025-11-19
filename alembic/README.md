# Alembic Migrations для Task Tracker

Этот проект использует Alembic для управления миграциями базы данных с SQLAlchemy.

## Настройка

Alembic настроен для работы с SQLAlchemy. 
Конфигурация базы данных берется из `src/config.py` (переменная `DATABASE_URL`).
SQLAlchemy модели для миграций находятся в `src/database/models.py`.

**Важно**: Приложение использует `asyncpg` для работы с БД, но SQLAlchemy используется только для миграций.

## Использование

### Активация виртуального окружения

```bash
source venv/bin/activate
```

### Основные команды

#### Создать новую миграцию (вручную)

```bash
alembic revision -m "описание изменений"
```

#### Создать миграцию автоматически (автогенерация)

```bash
# Alembic сравнит модели в src/database/models.py с БД
# и автоматически создаст миграцию с изменениями
alembic revision --autogenerate -m "описание изменений"
```

**Преимущество**: Не нужно писать SQL вручную! Просто измените модели и запустите автогенерацию.

#### Применить все миграции

```bash
alembic upgrade head
```

#### Применить конкретную миграцию

```bash
alembic upgrade <revision_id>
```

#### Откатить последнюю миграцию

```bash
alembic downgrade -1
```

#### Откатить все миграции

```bash
alembic downgrade base
```

#### Посмотреть текущую версию

```bash
alembic current
```

#### Посмотреть историю миграций

```bash
alembic history
```

#### Посмотреть SQL миграции (без применения)

```bash
alembic upgrade head --sql
```

## Структура миграций

Миграции находятся в `alembic/versions/`. Каждая миграция содержит:

- `revision`: Уникальный идентификатор миграции
- `down_revision`: Идентификатор предыдущей миграции (или `None` для первой)
- `upgrade()`: Функция для применения изменений
- `downgrade()`: Функция для отката изменений

## Важные замечания

1. **SQLAlchemy для миграций**: 
   - Используем SQLAlchemy только для миграций (не для работы с данными)
   - Приложение продолжает использовать `asyncpg` для всех операций с БД
   - SQLAlchemy модели в `src/database/models.py` используются только Alembic

2. **Автогенерация миграций**: 
   - ✅ Работает! Используйте `alembic revision --autogenerate`
   - Измените модели в `src/database/models.py`
   - Запустите автогенерацию - Alembic создаст миграцию автоматически

3. **SQLAlchemy операции**: 
   - Используйте `op.create_table()`, `op.add_column()` и т.д.
   - Или `op.execute()` для прямого SQL, если нужно

4. **Транзакции**: Alembic автоматически оборачивает миграции в транзакции.

## Примеры миграций

### Пример 1: Добавление колонки (SQLAlchemy операции)

```python
"""Add new column to users table

Revision ID: 002_add_phone
Revises: 001_initial
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union

revision: str = '002_add_phone'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add phone column to user table."""
    op.add_column('user', sa.Column('phone', sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Remove phone column from user table."""
    op.drop_column('user', 'phone')
```

### Пример 2: Автогенерация миграции

1. Измените модель в `src/database/models.py`:
```python
class User(Base):
    # ... существующие поля ...
    phone = Column(String(20), nullable=True)  # Добавили новое поле
```

2. Запустите автогенерацию:
```bash
alembic revision --autogenerate -m "add phone to users"
```

3. Alembic автоматически создаст миграцию с `op.add_column()`!

## Troubleshooting

### Ошибка импорта SQLAlchemy

Убедитесь, что SQLAlchemy установлен:
```bash
pip install -r requirements.txt
```

### Ошибка импорта моделей

Проверьте, что путь к `src/` правильный и модели находятся в `src/database/models.py`.

### Ошибка подключения к БД

Проверьте:
1. Правильность `DATABASE_URL` в `src/config.py` или переменной окружения
2. Что PostgreSQL запущен и доступен
3. Что база данных существует

### Миграция не применяется

Проверьте:
1. Что миграция находится в `alembic/versions/`
2. Что `revision` и `down_revision` правильно указаны
3. Используйте `alembic current` для проверки текущей версии


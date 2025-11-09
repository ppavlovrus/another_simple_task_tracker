# Доменная модель

Документ описывает структуру доменной модели трекера задач, включая модели (Entities), Value Objects, Domain Services и исключения.

**Дата создания:** 2025-01-XX  
**Версия:** 1.0

---

## Содержание

1. [Domain Models (Entities)](#domain-models-entities)
2. [Value Objects](#value-objects)
3. [Domain Services](#domain-services)
4. [Exceptions](#exceptions)
5. [Архитектурные принципы](#архитектурные-принципы)

---

## Domain Models (Entities)

### User

**Файл:** `src/domain/models/user.py`

**Описание:** Сущность пользователя системы.

**Атрибуты:**
- `id: int` - Уникальный идентификатор
- `name: str` - Полное имя пользователя
- `email: Email` - Email Value Object (валидированный и нормализованный)
- `password: str` - Хешированный пароль
- `created_at: datetime` - Время создания
- `updated_at: datetime` - Время последнего обновления

**Методы:**
- `update_email(new_email: Email)` - Обновление email адреса

**Пример использования:**
```python
from domain.value_objects.email import Email
from domain.models.user import User

email = Email("user@example.com")
user = User(
    id=1,
    name="John Doe",
    email=email,
    password="hashed_password",
    created_at=datetime.now(),
    updated_at=datetime.now()
)
```

---

### Task

**Файл:** `src/domain/models/task.py`

**Описание:** Сущность задачи. Основная бизнес-сущность системы.

**Атрибуты:**
- `id: int` - Уникальный идентификатор
- `title: TaskTitle` - Заголовок задачи (Value Object, валидированный)
- `description: Optional[str]` - Описание задачи
- `status: TaskStatus` - Текущий статус задачи
- `creator_id: int` - ID пользователя, создавшего задачу
- `assignee_id: Optional[int]` - ID назначенного исполнителя

**Статусы (TaskStatus):**
- `CREATED` - Задача создана
- `IN_PROGRESS` - Задача в работе
- `PAUSED` - Задача приостановлена
- `COMPLETED` - Задача завершена
- `CANCELLED` - Задача отменена

**Методы:**
- `update_title(new_title: TaskTitle, user_id: int, is_admin: bool)` - Обновление заголовка с проверкой прав
- `change_status(new_status: TaskStatus, user_id: int, is_admin: bool)` - Изменение статуса с валидацией
- `assign_to(assignee_id: int, user_id: int, is_admin: bool)` - Назначение исполнителя с проверкой прав
- `start_work(user_id: int, is_admin: bool)` - Начать работу над задачей (удобный метод)

**Бизнес-правила:**
- Согласно FR-1.2 и FR-5.1: только creator, assignee или admin могут редактировать задачу
- Согласно FR-5.2: только creator или admin могут назначать исполнителя
- Переходы статусов валидируются через `TaskStatusService`

**Пример использования:**
```python
from domain.value_objects.task_title import TaskTitle
from domain.models.task import Task, TaskStatus

title = TaskTitle("Implement feature X")
task = Task(
    id=1,
    title=title,
    description="Description",
    status=TaskStatus.CREATED,
    creator_id=123,
)

# Изменение статуса с валидацией
task.change_status(
    new_status=TaskStatus.IN_PROGRESS,
    user_id=123,
    is_admin=False
)
```

---

### TimeLog

**Файл:** `src/domain/models/time_log.py`

**Описание:** Сущность записи о затраченном времени на задачу.

**Атрибуты:**
- `id: int` - Уникальный идентификатор
- `task_id: int` - ID связанной задачи
- `user_id: int` - ID пользователя, зафиксировавшего время
- `duration: Duration` - Длительность (Value Object, валидированный)
- `comment: Optional[str]` - Комментарий о проделанной работе
- `logged_at: datetime` - Время фиксации

**Методы:**
- `get_duration_hours() -> float` - Получить длительность в часах
- `get_duration_minutes() -> float` - Получить длительность в минутах
- `get_duration_seconds() -> int` - Получить длительность в секундах

**Пример использования:**
```python
from domain.value_objects.duration import Duration
from domain.models.time_log import TimeLog

duration = Duration(3661)  # 1 час 1 минута 1 секунда
time_log = TimeLog(
    id=1,
    task_id=123,
    user_id=456,
    duration=duration,
    comment="Implemented feature",
    logged_at=datetime.now()
)

print(time_log.duration.hours)  # 1.0169444444444444
```

---

### Comment

**Файл:** `src/domain/models/comment.py`

**Описание:** Сущность комментария к задаче.

**Атрибуты:**
- `id: int` - Уникальный идентификатор
- `task_id: int` - ID связанной задачи
- `user_id: int` - ID пользователя, оставившего комментарий
- `content: str` - Текст комментария
- `created_at: datetime` - Время создания

**Бизнес-правила:**
- Согласно FR-3.1: любой авторизованный пользователь может добавлять комментарии
- Согласно FR-3.2: комментарии неизменяемы после создания
- Согласно FR-3.3: комментарии отображаются в хронологическом порядке

---

### Attachment

**Файл:** `src/domain/models/attachment.py`

**Описание:** Сущность прикрепленного файла к задаче.

**Атрибуты:**
- `id: int` - Уникальный идентификатор
- `task_id: int` - ID связанной задачи
- `user_id: int` - ID пользователя, загрузившего файл
- `filename: str` - Оригинальное имя файла
- `content_type: str` - MIME-тип файла
- `size_bytes: int` - Размер файла в байтах
- `storage_path: str` - Путь к файлу в хранилище
- `created_at: datetime` - Время загрузки

**Бизнес-правила:**
- Согласно FR-4.1: максимум 10 файлов на задачу
- Согласно FR-4.2: поддерживаемые форматы: .pdf, .txt, .docx, .png, .jpg, .jpeg
- Согласно FR-4.3: в БД хранятся только метаданные, файлы - в хранилище

---

### Activity

**Файл:** `src/domain/models/activity.py`

**Описание:** Сущность записи в журнале активности (audit log).

**Атрибуты:**
- `id: int` - Уникальный идентификатор
- `task_id: int` - ID связанной задачи
- `user_id: int` - ID пользователя, выполнившего действие
- `activity_type: ActivityType` - Тип активности
- `activity_data: Optional[Dict[str, Any]]` - Дополнительные данные
- `created_at: datetime` - Время создания записи

**Типы активности (ActivityType):**
- `TASK_CREATED` - Задача создана
- `TASK_UPDATED` - Задача обновлена
- `TASK_ASSIGNED` - Задача назначена
- `TASK_STATUS_CHANGED` - Статус задачи изменен
- `COMMENT_ADDED` - Добавлен комментарий
- `ATTACHMENT_ADDED` - Добавлен файл
- И другие...

**Бизнес-правила:**
- Согласно FR-7.1: система сохраняет журнал всех событий по задаче
- Согласно FR-7.2: доступен через API или UI как "история активности"

---

## Value Objects

Value Objects - это неизменяемые объекты, определяемые своими значениями. Они инкапсулируют бизнес-правила валидации и нормализации данных.

### Email

**Файл:** `src/domain/value_objects/email.py`

**Описание:** Value Object для email адресов.

**Валидация:**
- Проверка формата по RFC 5322
- Нормализация: автоматическое приведение к lowercase и обрезка пробелов

**Методы:**
- `value: str` - Получить нормализованный email

**Пример:**
```python
from domain.value_objects.email import Email

email = Email("  USER@EXAMPLE.COM  ")
print(email.value)  # "user@example.com"
```

---

### TaskTitle

**Файл:** `src/domain/value_objects/task_title.py`

**Описание:** Value Object для заголовков задач.

**Валидация:**
- Не может быть пустым
- Максимальная длина: 255 символов (FR-1.1)
- Автоматическая обрезка пробелов

**Методы:**
- `value: str` - Получить нормализованный заголовок

**Пример:**
```python
from domain.value_objects.task_title import TaskTitle

title = TaskTitle("  My Task  ")
print(title.value)  # "My Task"
```

---

### Duration

**Файл:** `src/domain/value_objects/duration.py`

**Описание:** Value Object для длительности времени.

**Валидация:**
- Не может быть отрицательным
- Максимум: 24 часа (86400 секунд)

**Методы:**
- `seconds: int` - Длительность в секундах
- `minutes: float` - Длительность в минутах
- `hours: float` - Длительность в часах
- `__add__(other: Duration)` - Сложение длительностей

**Пример:**
```python
from domain.value_objects.duration import Duration

duration = Duration(3661)  # 1 час 1 минута 1 секунда
print(duration.hours)  # 1.0169444444444444
print(duration.minutes)  # 61.016666666666666
print(str(duration))  # "1.02h"

# Сложение
total = duration + Duration(1800)  # + 30 минут
```

---

## Domain Services

Domain Services содержат бизнес-логику, которая не принадлежит одной Entity. Это операции, требующие нескольких сущностей или централизованной валидации.

### PermissionService

**Файл:** `src/domain/services/permission_service.py`

**Описание:** Сервис для проверки прав доступа к задачам.

**Методы:**
- `can_edit_task(user_id: int, task: Task, is_admin: bool) -> bool`
  - Проверяет, может ли пользователь редактировать задачу
  - Согласно FR-1.2 и FR-5.1: только creator, assignee или admin

- `can_delete_task(user_id: int, task: Task, is_admin: bool) -> bool`
  - Проверяет, может ли пользователь удалять задачу
  - Согласно FR-5.2: только creator или admin

- `can_change_assignee(user_id: int, task: Task, is_admin: bool) -> bool`
  - Проверяет, может ли пользователь менять исполнителя
  - Согласно FR-5.2: только creator или admin

**Пример:**
```python
from domain.services import PermissionService

if PermissionService.can_edit_task(user_id=123, task=task, is_admin=False):
    task.title = new_title
```

---

### TaskStatusService

**Файл:** `src/domain/services/task_status_service.py`

**Описание:** Сервис для валидации переходов статусов задач.

**Разрешенные переходы:**
- `CREATED` → `IN_PROGRESS`, `CANCELLED`
- `IN_PROGRESS` → `PAUSED`, `COMPLETED`, `CANCELLED`
- `PAUSED` → `IN_PROGRESS`, `CANCELLED`
- `COMPLETED` → (нет разрешенных переходов)
- `CANCELLED` → (нет разрешенных переходов)

**Методы:**
- `can_transition(current: TaskStatus, target: TaskStatus) -> bool`
  - Проверяет, возможен ли переход между статусами

- `validate_transition(task: Task, new_status: TaskStatus) -> None`
  - Валидирует переход и выбрасывает исключение если невалидно
  - Выбрасывает: `InvalidTaskStatusTransitionError`

**Пример:**
```python
from domain.services import TaskStatusService
from domain.models.task import TaskStatus

TaskStatusService.validate_transition(
    task=task,
    new_status=TaskStatus.IN_PROGRESS
)
```

---

### FileValidationService

**Файл:** `src/domain/services/file_validation_service.py`

**Описание:** Сервис для валидации файлов.

**Валидация:**
- Проверка расширения файла
- Проверка MIME-типа
- Проверка размера файла (максимум 10 MB)

**Поддерживаемые форматы (FR-4.2):**
- `.pdf` - `application/pdf`
- `.txt` - `text/plain`
- `.docx` - `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- `.png` - `image/png`
- `.jpg`, `.jpeg` - `image/jpeg`

**Методы:**
- `validate_file(filename: str, content_type: str, size_bytes: int) -> None`
  - Валидирует файл и выбрасывает исключения если невалидно
  - Выбрасывает: `UnsupportedFileTypeError`, `FileSizeExceededError`

**Пример:**
```python
from domain.services import FileValidationService

FileValidationService.validate_file(
    filename="document.pdf",
    content_type="application/pdf",
    size_bytes=1024 * 1024  # 1 MB
)
```

---

## Exceptions

Доменные исключения используются для выражения бизнес-правил и ошибок валидации.

### Структура исключений

**Базовый класс:** `DomainException` (`src/domain/exceptions/base.py`)

**Категории исключений:**

1. **Task Exceptions** (`task_exceptions.py`):
   - `TaskNotFoundError` - Задача не найдена
   - `TaskAlreadyArchivedError` - Задача уже архивирована
   - `InvalidTaskStatusTransitionError` - Недопустимый переход статуса
   - `TaskTitleTooLongError` - Заголовок слишком длинный

2. **Permission Exceptions** (`permission_exceptions.py`):
   - `PermissionDeniedError` - Общее исключение для прав доступа
   - `UnauthorizedTaskEditError` - Нет прав на редактирование задачи
   - `UnauthorizedTaskDeletionError` - Нет прав на удаление задачи
   - `UnauthorizedAssigneeChangeError` - Нет прав на изменение исполнителя

3. **File Exceptions** (`file_exceptions.py`):
   - `FileValidationError` - Общее исключение для файлов
   - `UnsupportedFileTypeError` - Неподдерживаемый тип файла
   - `FileSizeExceededError` - Размер файла превышает лимит
   - `MaxAttachmentsExceededError` - Превышен лимит файлов на задачу

4. **Validation Exceptions** (`validation_exceptions.py`):
   - `ValidationError` - Общее исключение валидации
   - `InvalidEmailError` - Невалидный email
   - `InvalidDurationError` - Невалидная длительность

**Пример использования:**
```python
from domain.exceptions import TaskNotFoundError, UnauthorizedTaskEditError

if not task:
    raise TaskNotFoundError(task_id=123)

if not PermissionService.can_edit_task(user_id, task):
    raise UnauthorizedTaskEditError(task_id=task.id, user_id=user_id)
```

---

## Архитектурные принципы

### Domain-Driven Design (DDD)

Проект следует принципам DDD:

1. **Entities (Сущности)** - объекты с уникальным идентификатором:
   - `User`, `Task`, `TimeLog`, `Comment`, `Attachment`, `Activity`

2. **Value Objects** - неизменяемые объекты, определяемые значениями:
   - `Email`, `TaskTitle`, `Duration`

3. **Domain Services** - бизнес-логика, не принадлежащая одной Entity:
   - `PermissionService`, `TaskStatusService`, `FileValidationService`

4. **Domain Events** - события домена (планируется для RabbitMQ):
   - `TaskAssignedEvent`, `CommentAddedEvent`, `TaskStatusChangedEvent`

### Принципы проектирования

1. **Инкапсуляция бизнес-правил** - правила валидации в Value Objects
2. **Централизация логики** - бизнес-логика в Domain Services
3. **Неизменяемость** - Value Objects неизменяемы после создания
4. **Валидация на уровне домена** - данные валидируются при создании
5. **Разделение ответственности** - четкое разделение между Entities, Value Objects и Services

### Соответствие требованиям

Все компоненты доменной модели соответствуют функциональным требованиям:

- **FR-1.1, FR-1.2** - Управление задачами (Task, TaskTitle, PermissionService)
- **FR-2.1, FR-2.2** - Временные затраты (TimeLog, Duration)
- **FR-3.1, FR-3.2, FR-3.3** - Комментарии (Comment)
- **FR-4.1, FR-4.2, FR-4.3** - Файлы (Attachment, FileValidationService)
- **FR-5.1, FR-5.2, FR-5.3** - Права доступа (PermissionService)
- **FR-7.1, FR-7.2** - История изменений (Activity)

---

## Структура файлов

```
src/domain/
├── models/              # Domain Models (Entities)
│   ├── user.py
│   ├── task.py
│   ├── time_log.py
│   ├── comment.py
│   ├── attachment.py
│   └── activity.py
├── value_objects/       # Value Objects
│   ├── email.py
│   ├── task_title.py
│   └── duration.py
├── services/            # Domain Services
│   ├── permission_service.py
│   ├── task_status_service.py
│   └── file_validation_service.py
└── exceptions/          # Domain Exceptions
    ├── base.py
    ├── task_exceptions.py
    ├── permission_exceptions.py
    ├── file_exceptions.py
    └── validation_exceptions.py
```

---

**Последнее обновление:** 2025-01-XX  
**Автор:** Development Team


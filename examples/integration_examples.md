# Примеры интеграции Value Objects и Domain Services

## Пример 1: User с Email Value Object

### До интеграции:
```python
# ❌ Проблемы:
# - Email не валидируется
# - Email не нормализуется
# - Можно создать User с невалидным email

user = User(
    id=1,
    name="John",
    email="  USER@EXAMPLE.COM  ",  # Не валидируется
    password="hashed",
    created_at=datetime.now(),
    updated_at=datetime.now()
)
```

### После интеграции:
```python
# ✅ Преимущества:
# - Email автоматически валидируется
# - Email нормализуется (lowercase, trim)
# - Нельзя создать User с невалидным email

from domain.value_objects.email import Email

# Email валидируется при создании
email = Email("  USER@EXAMPLE.COM  ")  # Станет "user@example.com"

user = User(
    id=1,
    name="John",
    email=email,  # Value Object
    password="hashed",
    created_at=datetime.now(),
    updated_at=datetime.now()
)

print(user.email.value)  # "user@example.com" (нормализован)
```

---

## Пример 2: Task с TaskTitle и Domain Services

### До интеграции:
```python
# ❌ Проблемы:
# - Title не валидируется
# - Нет проверки прав доступа
# - Нет валидации переходов статусов

task = Task(
    id=1,
    title="  My Task  ",  # Не валидируется
    description="Description",
    status=TaskStatus.CREATED,
    creator_id=123,
)

# ❌ Можно изменить статус без проверки
task.status = TaskStatus.COMPLETED  # Нет валидации

# ❌ Можно изменить title без проверки прав
task.title = "New Title"  # Нет проверки прав
```

### После интеграции:
```python
# ✅ Преимущества:
# - Title валидируется и обрезается
# - Проверка прав через Domain Service
# - Валидация переходов статусов

from domain.value_objects.task_title import TaskTitle
from domain.services.permission_service import PermissionService
from domain.services.task_status_service import TaskStatusService

# Title валидируется при создании
title = TaskTitle("  My Task  ")  # Станет "My Task"

task = Task(
    id=1,
    title=title,  # Value Object
    description="Description",
    status=TaskStatus.CREATED,
    creator_id=123,
)

# ✅ Изменение статуса с валидацией
task.change_status(
    new_status=TaskStatus.IN_PROGRESS,
    user_id=123,  # creator
    is_admin=False
)
# Автоматически проверяет:
# 1. Права доступа (PermissionService)
# 2. Валидность перехода (TaskStatusService)

# ✅ Обновление заголовка с проверкой прав
new_title = TaskTitle("Updated Task Title")
task.update_title(
    new_title=new_title,
    user_id=123,  # creator
    is_admin=False
)
# Автоматически проверяет права доступа
```

---

## Пример 3: TimeLog с Duration Value Object

### До интеграции:
```python
# ❌ Проблемы:
# - Duration не валидируется
# - Можно создать TimeLog с отрицательным временем
# - Нет удобных методов для работы со временем

time_log = TimeLog(
    id=1,
    task_id=123,
    user_id=456,
    duration_seconds=-100,  # ❌ Отрицательное значение!
    comment="Worked",
    logged_at=datetime.now()
)

# ❌ Ручной расчет
hours = time_log.duration_seconds / 3600
```

### После интеграции:
```python
# ✅ Преимущества:
# - Duration валидируется
# - Нельзя создать с отрицательным временем
# - Удобные методы для работы со временем

from domain.value_objects.duration import Duration

# Duration валидируется при создании
duration = Duration(3661)  # 1 час 1 минута 1 секунда

time_log = TimeLog(
    id=1,
    task_id=123,
    user_id=456,
    duration=duration,  # Value Object
    comment="Worked",
    logged_at=datetime.now()
)

# ✅ Удобные методы Value Object
print(time_log.duration.hours)  # 1.0169444444444444
print(time_log.duration.minutes)  # 61.016666666666666
print(str(time_log.duration))  # "1.02h"

# ✅ Сложение Duration
additional_time = Duration(1800)  # 30 минут
total = time_log.duration + additional_time  # 1.5 часа
```

---

## Пример 4: Использование Domain Services в сервисном слое

```python
from domain.services import PermissionService, TaskStatusService
from domain.models.task import Task, TaskStatus
from domain.value_objects.task_title import TaskTitle

def update_task_service(
    task_id: int,
    new_title: str,
    user_id: int,
    is_admin: bool,
    task_repository
) -> None:
    """Сервис для обновления задачи."""
    
    # Получаем задачу
    task = task_repository.get_by_id(task_id)
    if not task:
        raise TaskNotFoundError(task_id)
    
    # ✅ Проверка прав через Domain Service
    if not PermissionService.can_edit_task(
        user_id=user_id,
        task=task,
        is_admin=is_admin
    ):
        raise UnauthorizedTaskEditError(task_id=task_id, user_id=user_id)
    
    # ✅ Валидация title через Value Object
    title = TaskTitle(new_title)  # Валидируется автоматически
    
    # Обновляем задачу
    task.title = title
    task_repository.save(task)


def change_task_status_service(
    task_id: int,
    new_status: TaskStatus,
    user_id: int,
    is_admin: bool,
    task_repository
) -> None:
    """Сервис для изменения статуса задачи."""
    
    task = task_repository.get_by_id(task_id)
    if not task:
        raise TaskNotFoundError(task_id)
    
    # ✅ Проверка прав
    if not PermissionService.can_edit_task(
        user_id=user_id,
        task=task,
        is_admin=is_admin
    ):
        raise UnauthorizedTaskEditError(task_id=task_id, user_id=user_id)
    
    # ✅ Валидация перехода статуса
    TaskStatusService.validate_transition(
        task=task,
        new_status=new_status
    )
    
    # Обновляем статус
    task.status = new_status
    task_repository.save(task)
```

---

## Резюме преимуществ

### Value Objects:
1. ✅ Автоматическая валидация при создании
2. ✅ Нормализация данных (lowercase, trim)
3. ✅ Инкапсуляция бизнес-правил
4. ✅ Удобные методы работы со значениями
5. ✅ Неизменяемость (immutability)

### Domain Services:
1. ✅ Централизованная бизнес-логика
2. ✅ Переиспользуемость
3. ✅ Тестируемость
4. ✅ Четкое разделение ответственности
5. ✅ Соответствие принципам DDD


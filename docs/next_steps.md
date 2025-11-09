# Следующие шаги разработки

## Текущий статус

✅ **Готово:**
- Domain Layer (Models, Value Objects, Domain Services)
- Domain Exceptions
- Интерфейсы репозиториев (пустые файлы)
- Документация

## Что делать дальше: пошаговый план

### Шаг 1: Определить интерфейсы репозиториев

**Приоритет:** Высокий  
**Время:** 1-2 часа

Создать интерфейсы (абстрактные классы) для всех репозиториев:

```python
# src/interfaces/repositories/task_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from domain.models.task import Task

class TaskRepository(ABC):
    @abstractmethod
    def save(self, task: Task) -> None:
        """Сохранить задачу."""
        pass
    
    @abstractmethod
    def get_by_id(self, task_id: int) -> Optional[Task]:
        """Получить задачу по ID."""
        pass
    
    @abstractmethod
    def find_all(self, filters: dict) -> List[Task]:
        """Найти задачи по фильтрам."""
        pass
    
    @abstractmethod
    def delete(self, task_id: int) -> None:
        """Удалить задачу."""
        pass
```

**Нужно сделать для:**
- TaskRepository
- UserRepository
- TimeLogRepository
- CommentRepository
- AttachmentRepository
- ActivityRepository

---

### Шаг 2: Настроить проект (зависимости)

**Приоритет:** Высокий  
**Время:** 30 минут

Создать файлы для управления зависимостями:

1. **requirements.txt** или **pyproject.toml**
2. Установить зависимости:
   - SQLAlchemy
   - Alembic
   - FastAPI (или Flask)
   - Pydantic
   - pytest

---

### Шаг 3: Создать SQLAlchemy модели

**Приоритет:** Высокий  
**Время:** 2-3 часа

Создать ORM модели для всех Entities:

```python
# src/infrastructure/database/models/task_model.py
from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship

class TaskModel(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(TaskStatus), nullable=False)
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    assignee_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
```

---

### Шаг 4: Создать мапперы Domain <-> ORM

**Приоритет:** Высокий  
**Время:** 2-3 часа

Создать мапперы для преобразования между доменными объектами и ORM моделями:

```python
# src/infrastructure/database/mappers/task_mapper.py
class TaskMapper:
    def to_orm(self, task: Task) -> TaskModel:
        """Преобразовать доменный объект в ORM модель."""
        return TaskModel(
            id=task.id,
            title=task.title.value,  # Value Object -> string
            description=task.description,
            status=task.status,
            creator_id=task.creator_id,
            assignee_id=task.assignee_id,
        )
    
    def to_domain(self, task_model: TaskModel) -> Task:
        """Преобразовать ORM модель в доменный объект."""
        return Task(
            id=task_model.id,
            title=TaskTitle(task_model.title),  # string -> Value Object
            description=task_model.description,
            status=task_model.status,
            creator_id=task_model.creator_id,
            assignee_id=task_model.assignee_id,
        )
```

---

### Шаг 5: Реализовать репозитории

**Приоритет:** Высокий  
**Время:** 3-4 часа

Реализовать интерфейсы репозиториев с использованием SQLAlchemy:

```python
# src/infrastructure/database/repositories/task_repository_impl.py
class TaskRepositoryImpl(TaskRepository):
    def __init__(self, session: Session, mapper: TaskMapper):
        self.session = session
        self.mapper = mapper
    
    def save(self, task: Task) -> None:
        task_model = self.mapper.to_orm(task)
        self.session.merge(task_model)
        self.session.commit()
    
    def get_by_id(self, task_id: int) -> Optional[Task]:
        task_model = self.session.query(TaskModel).filter_by(id=task_id).first()
        if not task_model:
            return None
        return self.mapper.to_domain(task_model)
```

---

### Шаг 6: Создать первый Use Case

**Приоритет:** Средний  
**Время:** 1-2 часа

Создать пример Use Case для понимания паттерна:

```python
# src/application/use_cases/tasks/create_task.py
class CreateTaskUseCase:
    def __init__(
        self,
        task_repository: TaskRepository,
        user_repository: UserRepository,
    ):
        self.task_repository = task_repository
        self.user_repository = user_repository
    
    def execute(
        self,
        title: str,
        description: str,
        creator_id: int,
    ) -> Task:
        # Валидация через Value Object
        task_title = TaskTitle(title)
        
        # Проверка пользователя
        creator = self.user_repository.get_by_id(creator_id)
        if not creator:
            raise UserNotFoundError(creator_id)
        
        # Создание доменного объекта
        task = Task(
            id=self.task_repository.next_id(),
            title=task_title,
            description=description,
            status=TaskStatus.CREATED,
            creator_id=creator_id,
        )
        
        # Сохранение
        self.task_repository.save(task)
        
        return task
```

---

### Шаг 7: Настроить миграции (Alembic)

**Приоритет:** Средний  
**Время:** 1 час

Настроить Alembic для управления миграциями БД:

```bash
# Инициализация
alembic init alembic

# Создание первой миграции
alembic revision --autogenerate -m "Initial migration"

# Применение миграций
alembic upgrade head
```

---

### Шаг 8: Создать API endpoints (FastAPI)

**Приоритет:** Средний  
**Время:** 2-3 часа

Создать REST API для взаимодействия с приложением:

```python
# src/api/routes/tasks.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/")
async def create_task(
    request: CreateTaskRequest,
    use_case: CreateTaskUseCase = Depends(get_create_task_use_case),
):
    task = use_case.execute(
        title=request.title,
        description=request.description,
        creator_id=request.creator_id,
    )
    return TaskResponse.from_domain(task)
```

---

## Рекомендуемый порядок

1. ✅ **Шаг 1** - Интерфейсы репозиториев (быстро, важно)
2. ✅ **Шаг 2** - Настройка проекта (зависимости)
3. ✅ **Шаг 3** - SQLAlchemy модели (основа для БД)
4. ✅ **Шаг 4** - Мапперы (связь Domain <-> ORM)
5. ✅ **Шаг 5** - Реализация репозиториев (работа с БД)
6. ✅ **Шаг 6** - Первый Use Case (пример паттерна)
7. ✅ **Шаг 7** - Миграции (версионирование БД)
8. ✅ **Шаг 8** - API endpoints (взаимодействие)

---

## Что можно делать параллельно

- **Тесты** - писать тесты по мере создания компонентов
- **Документация** - обновлять документацию при изменениях
- **Интеграция RabbitMQ** - после создания Use Cases

---

## Важные принципы

1. **Сначала интерфейсы, потом реализации**
2. **Тесты пишутся вместе с кодом**
3. **Один компонент за раз** - не пытаться сделать все сразу
4. **Использовать существующие Value Objects и Domain Services**
5. **Следовать принципам DDD**

---

**С чего начать:** Рекомендую начать с **Шага 1** - определения интерфейсов репозиториев. Это быстро и даст понимание, какие методы нужны.


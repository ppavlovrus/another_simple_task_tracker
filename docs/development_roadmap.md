# План разработки проекта

## Текущий статус: Доменная модель готова ✅

После создания доменной модели (Entities, Value Objects, Domain Services) следующими шагами в DDD проектах являются:

---

## 1. Application Layer (Слой приложения) 🚧

**Что это:** Слой, который координирует работу доменных объектов для выполнения бизнес-сценариев (Use Cases).

### Структура:
```
src/application/
├── use_cases/
│   ├── tasks/
│   │   ├── create_task.py
│   │   ├── update_task.py
│   │   ├── delete_task.py
│   │   ├── assign_task.py
│   │   └── change_task_status.py
│   ├── users/
│   │   ├── create_user.py
│   │   └── update_user.py
│   ├── time_logs/
│   │   └── log_time.py
│   └── comments/
│       └── add_comment.py
└── services/
    └── task_service.py  # Application Service (координирует Use Cases)
```

### Что делать:
- **Use Cases** - каждый Use Case = одна бизнес-операция
  - `CreateTaskUseCase` - создание задачи
  - `UpdateTaskUseCase` - обновление задачи
  - `AssignTaskUseCase` - назначение задачи
  - И т.д.

- **Application Services** - координируют несколько Use Cases
  - `TaskApplicationService` - сервис для работы с задачами
  - `UserApplicationService` - сервис для работы с пользователями

### Пример Use Case:
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
        # 1. Валидация через Value Object
        task_title = TaskTitle(title)
        
        # 2. Проверка существования пользователя
        creator = self.user_repository.get_by_id(creator_id)
        if not creator:
            raise UserNotFoundError(creator_id)
        
        # 3. Создание доменного объекта
        task = Task(
            id=self.task_repository.next_id(),
            title=task_title,
            description=description,
            status=TaskStatus.CREATED,
            creator_id=creator_id,
        )
        
        # 4. Сохранение через репозиторий
        self.task_repository.save(task)
        
        return task
```

---

## 2. Infrastructure Layer (Инфраструктурный слой) 🚧

**Что это:** Реализация интерфейсов из `interfaces/` с использованием конкретных технологий.

### Структура:
```
src/infrastructure/
├── database/
│   ├── models/           # SQLAlchemy модели (ORM)
│   │   ├── user_model.py
│   │   ├── task_model.py
│   │   └── ...
│   ├── repositories/     # Реализация репозиториев
│   │   ├── task_repository_impl.py
│   │   ├── user_repository_impl.py
│   │   └── ...
│   └── mappers/          # Маппинг Domain <-> ORM
│       ├── task_mapper.py
│       └── user_mapper.py
├── storage/
│   └── file_storage_impl.py  # Реализация FileStorage
└── messaging/
    └── rabbitmq_publisher.py  # Реализация NotificationService
```

### Что делать:

#### 2.1. SQLAlchemy модели (ORM)
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
```

#### 2.2. Реализация репозиториев
```python
# src/infrastructure/database/repositories/task_repository_impl.py
class TaskRepositoryImpl(TaskRepository):
    def __init__(self, session: Session, mapper: TaskMapper):
        self.session = session
        self.mapper = mapper
    
    def save(self, task: Task) -> None:
        task_model = self.mapper.to_orm(task)
        self.session.add(task_model)
        self.session.commit()
    
    def get_by_id(self, task_id: int) -> Optional[Task]:
        task_model = self.session.query(TaskModel).filter_by(id=task_id).first()
        if not task_model:
            return None
        return self.mapper.to_domain(task_model)
```

#### 2.3. Маппинг Domain <-> ORM
```python
# src/infrastructure/database/mappers/task_mapper.py
class TaskMapper:
    def to_orm(self, task: Task) -> TaskModel:
        return TaskModel(
            id=task.id,
            title=task.title.value,  # Value Object -> string
            description=task.description,
            status=task.status,
            creator_id=task.creator_id,
            assignee_id=task.assignee_id,
        )
    
    def to_domain(self, task_model: TaskModel) -> Task:
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

## 3. Presentation Layer (API слой) 📋

**Что это:** REST API endpoints для взаимодействия с приложением.

### Структура:
```
src/api/
├── routes/
│   ├── tasks.py
│   ├── users.py
│   ├── time_logs.py
│   └── comments.py
├── schemas/              # Pydantic схемы для валидации запросов
│   ├── task_schemas.py
│   └── user_schemas.py
└── dependencies.py      # Dependency Injection
```

### Что делать:

#### 3.1. Pydantic схемы (FastAPI)
```python
# src/api/schemas/task_schemas.py
from pydantic import BaseModel, Field

class CreateTaskRequest(BaseModel):
    title: str = Field(..., max_length=255)
    description: str | None = None
    assignee_id: int | None = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: str
    creator_id: int
    assignee_id: int | None
```

#### 3.2. API endpoints
```python
# src/api/routes/tasks.py
from fastapi import APIRouter, Depends
from application.use_cases.tasks.create_task import CreateTaskUseCase

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=TaskResponse)
async def create_task(
    request: CreateTaskRequest,
    use_case: CreateTaskUseCase = Depends(get_create_task_use_case),
    current_user: User = Depends(get_current_user),
):
    task = use_case.execute(
        title=request.title,
        description=request.description,
        creator_id=current_user.id,
    )
    return TaskResponse.from_domain(task)
```

---

## 4. Database Migrations (Миграции БД) 📋

**Что это:** Версионирование схемы базы данных через Alembic.

### Что делать:
```bash
# Инициализация Alembic
alembic init alembic

# Создание миграции
alembic revision --autogenerate -m "Create tasks table"

# Применение миграций
alembic upgrade head
```

### Структура:
```
alembic/
├── versions/
│   └── 001_create_tasks_table.py
└── env.py
```

---

## 5. Testing (Тестирование) 📋

**Что это:** Unit и Integration тесты для всех слоев.

### Структура:
```
test/
├── unit/
│   ├── domain/
│   │   ├── test_models.py
│   │   ├── test_value_objects.py
│   │   └── test_services.py
│   └── application/
│       └── test_use_cases.py
├── integration/
│   ├── test_repositories.py
│   └── test_api.py
└── conftest.py
```

### Что делать:
- **Unit тесты** для доменного слоя (модели, Value Objects, Services)
- **Integration тесты** для репозиториев и API
- **Fixtures** для переиспользования тестовых данных

---

## 6. Configuration & Dependency Injection 📋

**Что это:** Настройка приложения и управление зависимостями.

### Структура:
```
src/
├── config/
│   ├── settings.py       # Настройки приложения
│   └── database.py      # Настройки БД
└── di/                   # Dependency Injection
    └── container.py      # DI контейнер
```

### Что делать:
- Настройки через environment variables
- DI контейнер для управления зависимостями
- Фабрики для создания Use Cases

---

## Рекомендуемый порядок реализации

### Этап 1: Репозитории (Infrastructure)
1. ✅ Создать SQLAlchemy модели
2. ✅ Реализовать маппинг Domain <-> ORM
3. ✅ Реализовать репозитории
4. ✅ Написать тесты для репозиториев

### Этап 2: Use Cases (Application)
1. ✅ Создать Use Cases для основных операций
2. ✅ Интегрировать с репозиториями
3. ✅ Написать тесты для Use Cases

### Этап 3: API (Presentation)
1. ✅ Создать Pydantic схемы
2. ✅ Создать API endpoints
3. ✅ Настроить Dependency Injection
4. ✅ Написать тесты для API

### Этап 4: Дополнительно
1. ✅ Миграции БД (Alembic)
2. ✅ Интеграция с RabbitMQ
3. ✅ Файловое хранилище
4. ✅ Аутентификация и авторизация

---

## Типичная архитектура DDD проекта

```
┌─────────────────────────────────────────┐
│     Presentation Layer (API)            │
│     - REST endpoints                    │
│     - Request/Response schemas          │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     Application Layer                   │
│     - Use Cases                         │
│     - Application Services              │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     Domain Layer                        │
│     - Entities                          │
│     - Value Objects                     │
│     - Domain Services                   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     Infrastructure Layer                │
│     - Repositories (реализация)         │
│     - Database (SQLAlchemy)             │
│     - External Services                 │
└─────────────────────────────────────────┘
```

---

## Следующие шаги

### Рекомендуется начать с:

1. **Интерфейсы репозиториев** - определить методы в `interfaces/repositories/`
2. **SQLAlchemy модели** - создать ORM модели
3. **Маппинг** - создать мапперы Domain <-> ORM
4. **Реализация репозиториев** - реализовать интерфейсы
5. **Первый Use Case** - создать `CreateTaskUseCase` как пример

---

**Последнее обновление:** 2025-01-XX


# Что означает `db_pool: Optional[asyncpg.Pool] = None`

## Код

```python
# Global connection pool
db_pool: Optional[asyncpg.Pool] = None
```

---

## Разбор по частям

### 1. `db_pool` - имя переменной

Это **имя переменной**, которая будет хранить connection pool (пул соединений с базой данных).

### 2. `: Optional[asyncpg.Pool]` - type hint (аннотация типа)

Это **type hint** (подсказка типа), которая говорит:
- Переменная может быть типа `asyncpg.Pool` (пул соединений)
- ИЛИ `None` (ничего)

`Optional[asyncpg.Pool]` - это сокращение для `Union[asyncpg.Pool, None]`

**Простыми словами:**
```python
# Это означает:
db_pool может быть:
  - asyncpg.Pool (когда пул создан)
  - None (когда пул еще не создан или закрыт)
```

### 3. `= None` - начальное значение

Это **начальное значение** переменной. При старте программы `db_pool` равен `None` (пул еще не создан).

### 4. `# Global connection pool` - комментарий

Комментарий, объясняющий, что это глобальная переменная для хранения connection pool.

---

## Что такое глобальная переменная?

**Глобальная переменная** - это переменная, объявленная на уровне модуля (не внутри функции), к которой можно обращаться из любой функции в этом модуле.

### Пример:

```python
# Глобальная переменная (на уровне модуля)
db_pool: Optional[asyncpg.Pool] = None

def function1():
    global db_pool  # Говорим, что используем глобальную переменную
    db_pool = create_pool()  # Изменяем глобальную переменную

def function2():
    if db_pool is None:  # Читаем глобальную переменную
        print("Pool not created")
    else:
        use_pool(db_pool)  # Используем глобальную переменную
```

---

## Как это используется в нашем коде?

### 1. В функции `lifespan` (создание пула):

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool  # Говорим, что будем изменять глобальную переменную
    
    # Создаем пул и сохраняем в глобальную переменную
    db_pool = await asyncpg.create_pool(...)
    # Теперь db_pool больше не None, а содержит пул соединений
    
    yield
    
    # Закрываем пул
    await db_pool.close()
    # db_pool все еще содержит объект пула, но он закрыт
```

### 2. В функции `get_db_connection` (использование пула):

```python
async def get_db_connection() -> asyncpg.Connection:
    # Проверяем, создан ли пул
    if db_pool is None:  # Если пул еще не создан
        raise HTTPException(...)  # Ошибка: пул не инициализирован
    
    # Используем пул для получения соединения
    async with db_pool.acquire() as connection:
        yield connection
```

---

## Почему `Optional[asyncpg.Pool]`?

Потому что пул **не всегда существует**:

### Временная линия:

```
1. Запуск программы:
   db_pool = None  ← Пул еще не создан

2. FastAPI вызывает lifespan():
   db_pool = await asyncpg.create_pool(...)  ← Пул создан
   db_pool теперь имеет тип asyncpg.Pool

3. Приложение работает:
   db_pool используется в get_db_connection()  ← Пул существует

4. Остановка приложения:
   await db_pool.close()  ← Пул закрыт, но объект все еще существует
   (хотя в нашем коде мы не устанавливаем db_pool = None после закрытия)
```

### Почему `None` в начале?

```python
db_pool: Optional[asyncpg.Pool] = None
```

**Причина:** При импорте модуля `main.py` пул еще не создан. Он создается только когда FastAPI вызывает `lifespan()` при старте приложения.

**Без `None`:**
```python
# ❌ НЕПРАВИЛЬНО:
db_pool: asyncpg.Pool  # Ошибка! Переменная не инициализирована
```

**С `None`:**
```python
# ✅ ПРАВИЛЬНО:
db_pool: Optional[asyncpg.Pool] = None  # Начальное значение - None
```

---

## Почему используется `global db_pool`?

В Python, если вы хотите **изменить** глобальную переменную внутри функции, нужно использовать ключевое слово `global`:

```python
db_pool: Optional[asyncpg.Pool] = None

def lifespan(app: FastAPI):
    # ❌ БЕЗ global:
    db_pool = create_pool()  # Это создаст ЛОКАЛЬНУЮ переменную!
    # Глобальная db_pool останется None

def lifespan(app: FastAPI):
    # ✅ С global:
    global db_pool  # Говорим: "используем глобальную переменную"
    db_pool = create_pool()  # Теперь изменяем глобальную переменную
```

### В нашем коде:

```61:71:src/main.py
    global db_pool

    # Startup: create connection pool
    db_pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=10,
        max_size=20,
        command_timeout=60,
        max_queries=50000,
        max_inactive_connection_lifetime=300.0,
    )
```

**Без `global db_pool`:**
- Python создал бы **локальную** переменную `db_pool` внутри функции
- Глобальная `db_pool` осталась бы `None`
- `get_db_connection()` не смог бы использовать пул

**С `global db_pool`:**
- Мы изменяем **глобальную** переменную
- Все функции могут использовать созданный пул

---

## Альтернатива: использование `app.state`

Вместо глобальной переменной можно использовать `app.state`:

```python
# Вместо глобальной переменной:
# db_pool: Optional[asyncpg.Pool] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаем пул и сохраняем в app.state
    app.state.db_pool = await asyncpg.create_pool(...)
    yield
    await app.state.db_pool.close()

async def get_db_connection(app: FastAPI = Depends(lambda: app)):
    if app.state.db_pool is None:
        raise HTTPException(...)
    async with app.state.db_pool.acquire() as connection:
        yield connection
```

**Преимущества `app.state`:**
- Не нужен `global`
- Более явная связь с приложением
- Лучше для тестирования

**Преимущества глобальной переменной:**
- Проще использовать (не нужно передавать `app`)
- Меньше кода
- Подходит для простых случаев

В нашем случае оба подхода валидны!

---

## Визуализация работы

```
┌─────────────────────────────────────────┐
│  Модуль main.py                         │
│                                         │
│  db_pool: Optional[asyncpg.Pool] = None │ ← Глобальная переменная
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ lifespan(app: FastAPI)            │  │
│  │   global db_pool                  │  │
│  │   db_pool = create_pool()         │  │ ← Изменяет глобальную
│  │   yield                            │  │
│  │   await db_pool.close()           │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ get_db_connection()               │  │
│  │   if db_pool is None:             │  │ ← Читает глобальную
│  │   async with db_pool.acquire():   │  │ ← Использует глобальную
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ create_task(..., conn)             │  │
│  │   # conn из get_db_connection()    │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## Полный пример с комментариями

```python
# ========== ОБЪЯВЛЕНИЕ ГЛОБАЛЬНОЙ ПЕРЕМЕННОЙ ==========
# Тип: Optional[asyncpg.Pool] - может быть Pool или None
# Начальное значение: None (пул еще не создан)
db_pool: Optional[asyncpg.Pool] = None

# ========== СОЗДАНИЕ ПУЛА (при старте приложения) ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool  # Говорим: "будем изменять глобальную переменную"
    
    # Создаем пул и сохраняем в глобальную переменную
    db_pool = await asyncpg.create_pool(...)
    # Теперь db_pool имеет тип asyncpg.Pool (не None!)
    
    yield  # Приложение работает
    
    # Закрываем пул
    await db_pool.close()

# ========== ИСПОЛЬЗОВАНИЕ ПУЛА (в endpoints) ==========
async def get_db_connection() -> asyncpg.Connection:
    # Проверяем, создан ли пул
    if db_pool is None:  # Если пул еще None (не создан)
        raise HTTPException(...)  # Ошибка
    
    # Используем пул для получения соединения
    async with db_pool.acquire() as connection:
        yield connection
```

---

## Резюме

1. **`db_pool`** - глобальная переменная для хранения connection pool
2. **`Optional[asyncpg.Pool]`** - тип: может быть `Pool` или `None`
3. **`= None`** - начальное значение (пул еще не создан)
4. **`global db_pool`** - нужно для изменения глобальной переменной внутри функции
5. **Использование:**
   - В `lifespan()` - создание и закрытие пула
   - В `get_db_connection()` - проверка и использование пула

Это стандартный паттерн для хранения ресурсов, которые создаются при старте приложения и используются во всех endpoints!


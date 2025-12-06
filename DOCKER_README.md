# 🐳 Docker для интеграционного тестирования

Быстрая инструкция по запуску Task Tracker API в Docker контейнере.

## ⚡ Быстрый старт

```bash
# 1. Убедитесь, что PostgreSQL запущен на localhost:5432
# 2. Создайте базу данных и примените миграции:
#    createdb task_tracker
#    alembic upgrade head

# 3. Запустите контейнер
docker-compose up --build

# 4. API будет доступен на http://localhost:8000
#    Документация: http://localhost:8000/docs
```

## 📝 Примеры запросов

```bash
# Создать пользователя
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password_hash": "hashed_password"
  }'

# Получить пользователя
curl http://localhost:8000/users/1

# Создать задачу
curl -X POST "http://localhost:8000/tasks/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "description": "Test description",
    "status_id": 1,
    "creator_id": 1
  }'
```

## 🔧 Настройка

Переменные окружения можно изменить в `docker-compose.yml` или передать через `-e`:

```bash
docker run -e DATABASE_PASSWORD=mypassword ...
```

## 📚 Подробная документация

См. [docs/docker_integration_testing.md](docs/docker_integration_testing.md)





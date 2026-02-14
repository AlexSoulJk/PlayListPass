# PlayListPass MVP

Агрегатор музыкальных плейлистов (Yandex, Spotify, VK).

## 🛠 Технический стек
- **Backend:** Python 3.11, FastAPI, SQLAlchemy (Async), PostgreSQL.
- **Frontend:** React, TypeScript, Vite, Mantine UI.
- **Infra:** Docker Compose, Nginx.

## 🚀 Быстрый старт

### Предварительные требования
1. Установленный **Docker Desktop** (и запущенный).
2. Созданный файл `.env` в папке `docker/`.

```
DB_NAME=mock_db_name
DB_USER=mock_user
DB_PASSWORD=secret_pass
DB_HOST=db
DB_PORT=5432

NGINX_EXTERNAL_PORT=your_port

FRONTEND_INTERNAL_PORT=your_port

BACKEND_INTERNAL_PORT=your_port
BACKEND_EXTERNAL_PORT=your_port
```

### 1. Первый запуск
Перейдите в папку с инфраструктурой и запустите сборку:

```bash
cd docker
docker-compose up --build
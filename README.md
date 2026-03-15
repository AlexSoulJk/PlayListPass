# PlayListPass MVP

PlayListPass — сервис для совместной работы с музыкальными плейлистами.

## Технический стек
- Backend: Python 3.11, FastAPI, SQLAlchemy (async), PostgreSQL.
- Frontend: React 19, TypeScript, Vite.
- Инфраструктура: Docker Compose, Nginx, Adminer.

## Быстрый запуск

### Предварительные условия
1. Установлен и запущен Docker Desktop.
2. В каталоге `docker/` создан файл `.env` с переменными окружения.

Пример:

```env
DB_NAME=playlistpass
DB_USER=postgres
DB_PASSWORD=secret_pass
DB_HOST=db
DB_PORT=5432

NGINX_EXTERNAL_PORT=8090
FRONTEND_INTERNAL_PORT=5173
BACKEND_INTERNAL_PORT=8000
BACKEND_EXTERNAL_PORT=8000
```

### Запуск

```bash
cd docker
docker-compose up --build
```

После запуска:
- Frontend: `http://localhost:8090`
- Backend API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Adminer: `http://localhost:8081`

Подробности по сервисам и URL находятся в [docs/docker.md](docs/docker.md).

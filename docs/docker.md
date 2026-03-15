# Docker и контейнеры

## Запуск

Из корня проекта:

```bash
cd docker
docker-compose up --build
```

## URL после запуска
- Frontend (через Nginx): `http://localhost:8090`
- Backend API: `http://localhost:8000`
- Swagger backend: `http://localhost:8000/docs`
- OpenAPI backend: `http://localhost:8000/openapi.json`
- Adminer: `http://localhost:8081`
- PostgreSQL (внешнее подключение): `localhost:5439`

## Подключение к Adminer

Параметры во входной форме Adminer:
- System: `PostgreSQL`
- Server: `db`
- Username: `postgres`
- Password: `secret_pass`
- Database: `playlistpass`

## Сервисы в Docker Compose
- `playlist_db` — PostgreSQL 16.2-alpine
- `playlist_backend` — FastAPI + Uvicorn (порт контейнера `8000`)
- `playlist_frontend` — Vite dev server (порт контейнера `5173`)
- `playlist_nginx` — gateway (внешний порт `8090`)
- `playlist_adminer` — Adminer (внешний порт `8081`)

## Важно про API через Nginx
- В `nginx/conf.d/default.conf` backend проксируется на путь `/api/`.
- При текущем `proxy_pass http://backend:8000;` префикс `/api` не отбрасывается, поэтому backend-ручки без `/api` могут быть недоступны через gateway.
- Для стабильной работы API/Swagger используйте прямой URL backend: `http://localhost:8000`.

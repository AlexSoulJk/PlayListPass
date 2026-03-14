# Docker / контейнеры

## Запуск
Из корня проекта:
```bash
cd docker
docker-compose up --build
```

## URL после запуска

- Frontend (через Nginx gateway): `http://localhost:8090`
- Backend API (прямой порт backend-контейнера): `http://localhost:8000`
- Swagger backend: `http://localhost:8000/docs`
- OpenAPI backend: `http://localhost:8000/openapi.json`
- Adminer: `http://localhost:8081`
- PostgreSQL (для внешнего клиента): `localhost:5439`

## Adminer (как подключаться)
В форме входа Adminer:
- System: `PostgreSQL`
- Server: `db`
- Username: `postgres`
- Password: `secret_pass`
- Database: `playlistpass`

## Сервисы и контейнеры
- `playlist_db` (PostgreSQL 16.2-alpine)
- `playlist_backend` (FastAPI + Uvicorn, порт контейнера `8000`)
- `playlist_frontend` (Vite dev server, порт контейнера `5173`)
- `playlist_nginx` (gateway, внешний порт `8090`)
- `playlist_adminer` (внешний порт `8081`)

## Важно по API через Nginx
- В `nginx/conf.d/default.conf` backend проксируется на путь `/api/`.
- В текущем виде `proxy_pass http://backend:8000;` не убирает префикс `/api`, поэтому backend ручки без префикса `/api` могут не открываться через gateway.
- Для работы API/Swagger без правок nginx используйте прямой backend URL: `http://localhost:8000`.

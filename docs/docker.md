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
- MinIO S3 API: `http://localhost:9000`
- MinIO Console: `http://localhost:9001`
- S3 proxy через Nginx (для presigned/public URL): `http://localhost:8090/s3/...`
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
- `playlist_minio` — локальное S3-совместимое хранилище MinIO (`9000` API, `9001` Console)
- `playlist_minio_init` — одноразовая инициализация MinIO (создание bucket + публичный read policy)

## Важно про API через Nginx
- В `nginx/conf.d/default.conf` backend проксируется на путь `/api/`.
- При текущем `proxy_pass http://backend:8000;` префикс `/api` не отбрасывается, поэтому backend-ручки без `/api` могут быть недоступны через gateway.
- Для стабильной работы API/Swagger используйте прямой URL backend: `http://localhost:8000`.

## Важно про загрузку картинок (группы)
- Backend работает с MinIO по внутреннему адресу `http://minio:9000`.
- Клиент (браузер) получает presigned/public URL на `http://localhost:8090/s3/...`.
- Путь `/s3/` проксируется Nginx в MinIO, поэтому загрузка картинки работает как same-origin относительно frontend.

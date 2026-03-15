# Структура тестов Frontend

- `components/` — изолированные unit-тесты компонентов.
- `pages/` — тесты страниц с проверкой поведения и навигации.
- `router/` — тесты роутинга и guard-логики.
- `setup/` — общая инициализация тестового окружения.
- `utils/` — вспомогательные функции для тестов.
- `docs/` — markdown-сценарии, которые покрываются тестами.

## Как запускать тесты в контейнере

Из корня проекта:

```bash
cd docker
docker-compose up --build
```

Запуск всех тестов один раз:

```bash
docker exec playlist_frontend npm run test:run
```

Запуск тестов в watch-режиме:

```bash
docker exec playlist_frontend npm run test
```

Запуск production-сборки после тестов:

```bash
docker exec playlist_frontend npm run build
```

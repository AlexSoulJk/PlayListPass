# Документация Backend

## Базовые URL
- Backend API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Авторизация
- Используется JWT Bearer (`fastapi-users`).
- Получение токена: `POST /auth/jwt/login`.
- Передача токена в защищенные ручки: заголовок `Authorization: Bearer <access_token>`.

## Текущие ручки

### 1. Регистрация пользователя
- Метод и путь: `POST /auth/register`
- Авторизация: не требуется
- Вход (JSON):

```json
{
  "email": "user@example.com",
  "password": "string",
  "name": "Иван"
}
```

- Выход (`201 Created`):

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false,
  "name": "Иван"
}
```

### 2. Логин (получение JWT)
- Метод и путь: `POST /auth/jwt/login`
- Авторизация: не требуется
- Вход (`application/x-www-form-urlencoded`):

```text
username=<email>
password=<password>
grant_type=password
scope=
client_id=
client_secret=
```

- Минимально обязательные поля: `username`, `password`
- Выход (`200 OK`):

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

### 3. Логаут
- Метод и путь: `POST /auth/jwt/logout`
- Авторизация: требуется Bearer токен
- Тело запроса: не требуется
- Ответ: `204 No Content`

### 4. Тест защищенной ручки
- Метод и путь: `GET /auth_test/authenticated-route`
- Авторизация: требуется Bearer токен активного пользователя
- Ответ (`200 OK`):

```json
{
  "message": "Hello user@example.com!"
}
```

## Примечания
- В `backend/main.py` подключены роутеры `auth` и `auth_test`.
- На текущий момент это актуальный набор backend-эндпоинтов в проекте.

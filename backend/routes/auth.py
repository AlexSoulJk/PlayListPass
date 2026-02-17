from fastapi import APIRouter
from services.auth import auth_backend, fastapi_users
from schemas.auth import UserRead, UserCreate

# Создаём отдельный роутер для авторизации
auth_router = APIRouter(prefix="/auth", tags=["Auth"])

# Подключаем маршруты от fastapi_users
auth_router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",  # будет /auth/jwt/login, /auth/jwt/logout
)

auth_router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="",      # будет /auth/register
)
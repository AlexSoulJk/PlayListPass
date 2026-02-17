import uuid
from typing import Optional
from fastapi_users import schemas


# 1. Чтение (Read)
class UserRead(schemas.BaseUser[uuid.UUID]):
    name: str  # Мы хотим отдавать имя фронту

    class Config:
        from_attributes = True


# 2. Создание (Create / Register)
class UserCreate(schemas.BaseUserCreate):
    name: str


# 3. Обновление (Update)
class UserUpdate(schemas.BaseUserUpdate):
    name: Optional[str] = None

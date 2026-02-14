from fastapi import APIRouter, Depends, HTTPException
from schemas.auth import UserLoginSchema, UserResponseSchema
from services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=UserResponseSchema)
async def login(
    body: UserLoginSchema,
    # В будущем тут можно инжектить зависимость от БД: session = Depends(get_db)
):
    """
    Моковая ручка авторизации.
    Принимает email/password, отдает статус.
    """
    # 1. Вызываем сервис (бизнес-логику)
    result = await AuthService.mock_authenticate_user(body)
    
    # 2. Возвращаем результат
    return result
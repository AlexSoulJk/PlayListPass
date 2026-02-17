from fastapi import APIRouter, Depends
from services.auth import fastapi_users

# Создаём отдельный роутер для авторизации
router = APIRouter(prefix="/auth_test", tags=["Test"])
@router.get("/authenticated-route")
async def authenticated_route(user = Depends(fastapi_users.current_user(active=True))):
    return {"message": f"Hello {user.email}!"}
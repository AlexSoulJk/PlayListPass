from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from services.settings import settings

# Создаем движок
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Фабрика сессий
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# Dependency для FastAPI
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
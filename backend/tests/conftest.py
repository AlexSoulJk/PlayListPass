import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool


os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "playlistpass_test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from database.models.base import Base  # noqa: E402
from database.models import models as _models  # noqa: E402,F401
from database.session import get_async_session  # noqa: E402
from main import app  # noqa: E402


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionMaker = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionMaker() as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database() -> AsyncGenerator[None, None]:
    app.dependency_overrides[get_async_session] = override_get_async_session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    app.dependency_overrides.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture(autouse=True)
async def reset_database() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionMaker() as session:
        yield session

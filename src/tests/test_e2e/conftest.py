import uuid

import httpx
import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config.settings import get_settings


settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture
async def client():
    async with httpx.AsyncClient(
        base_url="http://localhost:8000/api/v1",
        timeout=30.0,
    ) as client:
        yield client


@pytest_asyncio.fixture
async def mailhog_client():
    async with httpx.AsyncClient(
        base_url="http://localhost:8025/api/v2",
        timeout=30.0,
    ) as client:
        yield client


@pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
def unique_email():
    return f"test_{uuid.uuid4().hex}@example.com"


@pytest.fixture
def user_password():
    return "TestPassword123!"

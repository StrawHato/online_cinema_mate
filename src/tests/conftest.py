from collections.abc import AsyncGenerator
import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config.settings import get_settings, Settings
from src.security.interfaces import JWTAuthManagerInterface
from src.security.token_manager import JWTAuthManager
from src.config.dependencies import (
    get_accounts_email_notificator,
    get_storage,
    get_stripe_service,
)
from src.database.models import (
    Base,
    UserGroupEnum,
    UserGroupModel,
)
from src.database.session import get_db
from src.main import app
from src.tests.doubles.fakes.storage import FakeS3Storage
from src.tests.doubles.stubs.emails import StubEmailSender
from src.tests.doubles.stubs.stripe import StubStripeService

TEST_DATABASE_PATH = "tests/test.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DATABASE_PATH}"

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "unit: Unit tests",
    )

    config.addinivalue_line(
        "markers",
        "integration: Integration tests",
    )

    config.addinivalue_line(
        "markers",
        "e2e: End-to-end tests",
    )


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """
    Create a fresh SQLite database before the test session
    and remove it after all tests complete.
    """
    if os.path.exists(TEST_DATABASE_PATH):
        os.remove(TEST_DATABASE_PATH)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()

    if os.path.exists(TEST_DATABASE_PATH):
        os.remove(TEST_DATABASE_PATH)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clean_database() -> AsyncGenerator[None, None]:
    """
    Remove all data from every table before each test.
    """
    async with TestingSessionLocal() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())

        await session.commit()

    yield


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session for tests.
    """
    async with TestingSessionLocal() as session:
        yield session


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def email_sender_stub() -> StubEmailSender:
    return StubEmailSender()


@pytest_asyncio.fixture(scope="function")
async def storage_fake() -> FakeS3Storage:
    return FakeS3Storage()


@pytest_asyncio.fixture(scope="function")
async def stripe_stub() -> StubStripeService:
    return StubStripeService()


@pytest_asyncio.fixture(scope="function")
async def client(
    email_sender_stub: StubEmailSender,
    storage_fake: FakeS3Storage,
    stripe_stub: StubStripeService,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client with overridden dependencies.
    """
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[
        get_accounts_email_notificator
    ] = lambda: email_sender_stub

    app.dependency_overrides[
        get_storage
    ] = lambda: storage_fake

    app.dependency_overrides[
        get_stripe_service
    ] = lambda: stripe_stub

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as async_client:
        try:
            yield async_client
        finally:
            app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def user_groups(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Seed default user groups.
    """
    groups = [
        {"name": group.value}
        for group in UserGroupEnum
    ]

    await db_session.execute(
        insert(UserGroupModel).values(groups)
    )

    await db_session.commit()

    yield db_session


@pytest_asyncio.fixture(scope="session")
async def settings() -> Settings:
    """
    Return application settings.
    """
    return get_settings()


@pytest_asyncio.fixture(scope="function")
async def jwt_manager(
    settings: Settings,
) -> JWTAuthManagerInterface:
    """
    Return JWT manager configured for tests.
    """
    return JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
    )

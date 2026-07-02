from collections.abc import AsyncGenerator
import os
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import joinedload

from src.database.models import UserProfileModel
from src.security.http import get_current_admin, get_current_user
from src.database.models import UserModel
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

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TEST_DATABASE_PATH = PROJECT_ROOT / "test.db"

TEST_DATABASE_URL = (
    f"sqlite+aiosqlite:///{TEST_DATABASE_PATH.as_posix()}"
)
TEST_DATABASE_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

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
            transport=ASGITransport(
                app=app,
                raise_app_exceptions=True,
            ),
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


@pytest_asyncio.fixture(scope="function")
async def admin_user(
    db_session: AsyncSession,
    user_groups: AsyncSession,
) -> UserModel:
    """
    Create admin user.
    """
    group = await db_session.scalar(
        select(UserGroupModel).where(
            UserGroupModel.name == UserGroupEnum.ADMIN
        )
    )

    admin = UserModel.create(
        email="admin@example.com",
        raw_password="AdminPassword123!",
        group_id=group.id,
    )

    admin.is_active = True

    db_session.add(admin)

    await db_session.commit()

    result = await db_session.execute(
        select(UserModel)
        .options(
            joinedload(UserModel.group),
            joinedload(UserModel.profile),
        )
        .where(UserModel.id == admin.id)
    )

    return result.unique().scalar_one()


@pytest_asyncio.fixture(scope="function")
async def admin_client(
    client: AsyncClient,
    admin_user: UserModel,
):
    app.dependency_overrides[
        get_current_user
    ] = lambda: admin_user

    app.dependency_overrides[
        get_current_admin
    ] = lambda: admin_user

    yield client

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )

    app.dependency_overrides.pop(
        get_current_admin,
        None,
    )


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


@pytest.fixture(scope="function", autouse=True)
def mock_celery_tasks():
    """
    Disable all Celery tasks during integration tests.
    Tasks are replaced with mocks, so no Redis,
    no asyncio.run(), and no external side effects.
    """
    with (
        patch("src.services.accounts.send_activation_email_task") as activation_email,
        patch("src.services.accounts.send_activation_complete_email_task") as activation_complete_email,
        patch("src.services.accounts.send_password_reset_email_task") as password_reset_email,
        patch("src.services.accounts.send_password_reset_complete_email_task") as password_reset_complete_email,

        patch("src.services.payments.send_payment_success_email_task") as payment_success_email,
        patch("src.services.payments.send_payment_refunded_email_task") as payment_refunded_email,

        patch("src.services.movies.send_comment_reply_email_task") as comment_reply_email,
        patch("src.services.movies.send_comment_like_email_task") as comment_like_email,

    ):
        yield


@pytest_asyncio.fixture(scope="function")
async def regular_user(
    db_session: AsyncSession,
    user_groups: AsyncSession,
) -> UserModel:
    group = await db_session.scalar(
        select(UserGroupModel).where(
            UserGroupModel.name == UserGroupEnum.USER
        )
    )

    user = UserModel.create(
        email="user@example.com",
        raw_password="StrongPassword123!",
        group_id=group.id,
    )

    user.is_active = True

    db_session.add(user)
    await db_session.flush()

    profile = UserProfileModel(
        user_id=user.id,
        username=user.email.split("@")[0],
    )

    db_session.add(profile)

    await db_session.commit()

    result = await db_session.execute(
        select(UserModel)
        .options(
            joinedload(UserModel.profile),
            joinedload(UserModel.group),
        )
        .where(UserModel.id == user.id)
    )

    return result.unique().scalar_one()


@pytest_asyncio.fixture(scope="function")
async def user_client(
    client: AsyncClient,
    regular_user: UserModel,
):
    app.dependency_overrides[
        get_current_user
    ] = lambda: regular_user

    yield client

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )

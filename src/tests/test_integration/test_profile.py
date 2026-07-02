from io import BytesIO

import pytest
from PIL import Image
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import UserModel, UserProfileModel


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_profile_success(
    user_client: AsyncClient,
    regular_user: UserModel,
):
    response = await user_client.get("/api/v1/profile/")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == regular_user.profile.id
    assert data["user_id"] == regular_user.id
    assert data["username"] == regular_user.profile.username
    assert data["first_name"] is None
    assert data["last_name"] is None
    assert data["gender"] is None
    assert data["date_of_birth"] is None
    assert data["info"] is None
    assert data["avatar"] is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_profile_unauthorized(
    client: AsyncClient,
):
    response = await client.get("/api/v1/profile/")

    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_profile_success(
    user_client: AsyncClient,
    regular_user: UserModel,
    db_session: AsyncSession,
):
    response = await user_client.patch(
        "/api/v1/profile/",
        data={
            "username": "maxim",
            "first_name": "Max",
            "last_name": "Ivanov",
            "gender": "man",
            "date_of_birth": "2000-05-12",
            "info": "Backend developer",
        },
        files={},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "maxim"
    assert data["first_name"] == "Max"
    assert data["last_name"] == "Ivanov"
    assert data["gender"] == "man"
    assert data["date_of_birth"] == "2000-05-12"
    assert data["info"] == "Backend developer"

    profile = await db_session.scalar(
        select(UserProfileModel).where(
            UserProfileModel.user_id == regular_user.id
        )
    )

    assert profile.username == "maxim"
    assert profile.first_name == "Max"
    assert profile.last_name == "Ivanov"
    assert profile.gender.value == "man"
    assert str(profile.date_of_birth) == "2000-05-12"
    assert profile.info == "Backend developer"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_profile_partial_update(
    user_client: AsyncClient,
    regular_user: UserModel,
    db_session: AsyncSession,
):
    regular_user.profile.first_name = "Old"
    regular_user.profile.last_name = "Surname"

    await db_session.commit()

    response = await user_client.patch(
        "/api/v1/profile/",
        data={
            "username": "maxim",
            "first_name": "New",
            "last_name": "White",
        },
        files={},
    )

    assert response.status_code == 200

    profile = await db_session.scalar(
        select(UserProfileModel).where(
            UserProfileModel.user_id == regular_user.id
        )
    )

    assert profile.first_name == "New"
    assert profile.last_name == "White"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_profile_username_already_exists(
    user_client: AsyncClient,
    db_session: AsyncSession,
    regular_user: UserModel,
    user_groups,
):
    second_user = UserModel.create(
        email="second@example.com",
        raw_password="StrongPassword123!",
        group_id=regular_user.group_id,
    )
    second_user.is_active = True

    db_session.add(second_user)
    await db_session.flush()

    second_profile = UserProfileModel(
        user_id=second_user.id,
        username="existingusername",
    )

    db_session.add(second_profile)
    await db_session.commit()

    response = await user_client.patch(
        "/api/v1/profile/",
        data={
            "username": "existingusername",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Username already exists.",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_profile_avatar(
    user_client: AsyncClient,
):
    image = Image.new("RGB", (1, 1), color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    response = await user_client.patch(
        "/api/v1/profile/",
        files={
            "avatar": (
                "avatar.png",
                buffer.getvalue(),
                "image/png",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["avatar"].startswith("avatars/")
    assert data["avatar"].endswith("_avatar.png")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_profile_unauthorized(
    client: AsyncClient,
):
    response = await client.patch(
        "/api/v1/profile/",
        data={
            "first_name": "Max",
        },
    )

    assert response.status_code == 401

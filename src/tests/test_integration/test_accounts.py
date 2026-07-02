from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import delete, select

from src.database.models.accounts import (
    ActivationTokenModel,
    PasswordResetTokenModel,
    RefreshTokenModel,
    UserGroupEnum,
    UserGroupModel,
    UserModel,
    UserProfileModel,
)
from src.tests.conftest import TestingSessionLocal

REGISTER_URL = "/api/v1/accounts/register/"
ACTIVATE_URL = "/api/v1/accounts/activate/"
LOGIN_URL = "/api/v1/accounts/login/"
REFRESH_URL = "/api/v1/accounts/refresh/"
PASSWORD_RESET_REQUEST_URL = "/api/v1/accounts/password-reset/request/"
PASSWORD_RESET_COMPLETE_URL = "/api/v1/accounts/reset-password/complete/"
RESEND_ACTIVATION_URL = "/api/v1/accounts/activation/resend/"
LOGOUT_URL = "/api/v1/accounts/logout/"


def registration_data(**kwargs):
    data = {
        "email": "user@example.com",
        "password": "StrongPassword123!",
    }
    data.update(kwargs)
    return data


async def activate_registered_user(client, db_session):
    await client.post(
        REGISTER_URL,
        json=registration_data(),
    )

    result = await db_session.execute(
        select(UserModel).where(
            UserModel.email == "user@example.com"
        )
    )

    user = result.scalar_one()

    result = await db_session.execute(
        select(ActivationTokenModel).where(
            ActivationTokenModel.user_id == user.id
        )
    )

    token = result.scalar_one()

    await client.post(
        ACTIVATE_URL,
        json={
            "email": user.email,
            "token": token.token,
        },
    )

    await db_session.refresh(user)

    return user


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_user_success(
    client,
    db_session,
    user_groups,
):
    response = await client.post(
        REGISTER_URL,
        json=registration_data(),
    )

    print(response.status_code)
    print(response.content)
    print(response.json())

    assert response.status_code == 201

    body = response.json()

    assert body["email"] == "user@example.com"
    assert body["is_active"] is False

    result = await db_session.execute(
        select(UserModel).where(
            UserModel.email == "user@example.com"
        )
    )

    user = result.scalar_one()

    assert user.verify_password(
        "StrongPassword123!"
    )

    result = await db_session.execute(
        select(UserProfileModel).where(
            UserProfileModel.user_id == user.id
        )
    )

    assert result.scalar_one_or_none() is not None

    result = await db_session.execute(
        select(ActivationTokenModel).where(
            ActivationTokenModel.user_id == user.id
        )
    )

    assert result.scalar_one_or_none() is not None

    group = await db_session.scalar(
        select(UserGroupModel).where(
            UserGroupModel.id == user.group_id
        )
    )

    assert group.name == UserGroupEnum.USER


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_existing_email(
    client,
    db_session,
    user_groups,
):
    await client.post(
        REGISTER_URL,
        json=registration_data(),
    )

    response = await client.post(
        REGISTER_URL,
        json=registration_data(),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "A user with this email user@example.com already exists."
    )

    result = await db_session.execute(
        select(UserModel)
    )

    assert len(result.scalars().all()) == 1


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email",
    [
        "test",
        "test@",
        "@gmail.com",
        "gmail.com",
    ],
)
async def test_register_invalid_email(
    email,
    client,
    db_session,
    user_groups,
):
    response = await client.post(
        REGISTER_URL,
        json=registration_data(
            email=email,
        ),
    )

    assert response.status_code == 422

    result = await db_session.execute(
        select(UserModel)
    )

    assert result.scalars().all() == []


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "password",
    [
        "",
        "123",
        "password",
        "PASSWORD",
        "Password",
        "12345678",
    ],
)
async def test_register_invalid_password(
    password,
    client,
    db_session,
    user_groups,
):
    response = await client.post(
        REGISTER_URL,
        json=registration_data(
            password=password,
        ),
    )

    assert response.status_code == 422

    result = await db_session.execute(
        select(UserModel)
    )

    assert result.scalars().all() == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_without_default_group(
    client,
    db_session,
):
    await db_session.execute(
        delete(UserGroupModel)
    )

    await db_session.commit()

    response = await client.post(
        REGISTER_URL,
        json=registration_data(),
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Default user group not found."


@pytest.mark.integration
@pytest.mark.asyncio
async def test_activate_success(
    client,
    db_session,
    user_groups,
):
    await client.post(
        REGISTER_URL,
        json=registration_data(),
    )

    user = await db_session.scalar(
        select(UserModel).where(
            UserModel.email == "user@example.com"
        )
    )

    token = await db_session.scalar(
        select(ActivationTokenModel).where(
            ActivationTokenModel.user_id == user.id
        )
    )

    response = await client.post(
        ACTIVATE_URL,
        json={
            "email": user.email,
            "token": token.token,
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": "User account activated successfully."
    }

    user_id = user.id

    async with TestingSessionLocal() as verify_session:
        updated_user = await verify_session.scalar(
            select(UserModel).where(
                UserModel.id == user_id
            )
        )

        assert updated_user.is_active is True

        activation_token = await verify_session.scalar(
            select(ActivationTokenModel).where(
                ActivationTokenModel.user_id == user_id
            )
        )

        assert activation_token is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_success(
    client,
    db_session,
    user_groups,
):
    user = await activate_registered_user(
        client,
        db_session,
    )

    response = await client.post(
        LOGIN_URL,
        json={
            "email": user.email,
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"

    result = await db_session.execute(
        select(RefreshTokenModel).where(
            RefreshTokenModel.user_id == user.id
        )
    )

    refresh_token = result.scalar_one_or_none()

    assert refresh_token is not None
    assert refresh_token.token == body["refresh_token"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_invalid_email(
    client,
    user_groups,
):
    response = await client.post(
        LOGIN_URL,
        json={
            "email": "missing@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid email or password."
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_invalid_password(
    client,
    db_session,
    user_groups,
):
    user = await activate_registered_user(
        client,
        db_session,
    )

    response = await client.post(
        LOGIN_URL,
        json={
            "email": user.email,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid email or password."
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_inactive_user(
    client,
    user_groups,
):
    await client.post(
        REGISTER_URL,
        json=registration_data(),
    )

    response = await client.post(
        LOGIN_URL,
        json={
            "email": "user@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": "User account is not activated."
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_invalid_schema(
    client,
):
    response = await client.post(
        LOGIN_URL,
        json={
            "email": "user@example.com",
        },
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refresh_access_token_success(
    client,
    db_session,
    user_groups,
):
    user = await activate_registered_user(
        client,
        db_session,
    )

    login_response = await client.post(
        LOGIN_URL,
        json={
            "email": user.email,
            "password": "StrongPassword123!",
        },
    )

    refresh_token = login_response.json()["refresh_token"]

    response = await client.post(
        REFRESH_URL,
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["access_token"]
    assert body["token_type"] == "bearer"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refresh_invalid_token(
    client,
):
    response = await client.post(
        REFRESH_URL,
        json={
            "refresh_token": "invalid",
        },
    )

    assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refresh_deleted_token(
    client,
    db_session,
    user_groups,
):
    user = await activate_registered_user(
        client,
        db_session,
    )

    login_response = await client.post(
        LOGIN_URL,
        json={
            "email": user.email,
            "password": "StrongPassword123!",
        },
    )

    refresh_token = login_response.json()["refresh_token"]

    token = await db_session.scalar(
        select(RefreshTokenModel).where(
            RefreshTokenModel.token == refresh_token
        )
    )

    await db_session.delete(token)
    await db_session.commit()

    response = await client.post(
        REFRESH_URL,
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Refresh token not found."
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_password_reset_success(
    client,
    db_session,
    user_groups,
):
    user = await activate_registered_user(
        client,
        db_session,
    )

    response = await client.post(
        PASSWORD_RESET_REQUEST_URL,
        json={
            "email": user.email,
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": (
            "If you are registered, "
            "you will receive an email with instructions."
        )
    }

    token = await db_session.scalar(
        select(PasswordResetTokenModel).where(
            PasswordResetTokenModel.user_id == user.id
        )
    )

    assert token is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_password_reset_unknown_email(
    client,
):
    response = await client.post(
        PASSWORD_RESET_REQUEST_URL,
        json={
            "email": "unknown@example.com",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": (
            "If you are registered, "
            "you will receive an email with instructions."
        )
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_password_reset_inactive_user(
    client,
    user_groups,
):
    await client.post(
        REGISTER_URL,
        json=registration_data(),
    )

    response = await client.post(
        PASSWORD_RESET_REQUEST_URL,
        json={
            "email": "user@example.com",
        },
    )

    assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reset_password_success(
    client,
    db_session,
    user_groups,
):
    user = await activate_registered_user(
        client,
        db_session,
    )

    await client.post(
        PASSWORD_RESET_REQUEST_URL,
        json={
            "email": user.email,
        },
    )

    token = await db_session.scalar(
        select(PasswordResetTokenModel).where(
            PasswordResetTokenModel.user_id == user.id
        )
    )

    response = await client.post(
        PASSWORD_RESET_COMPLETE_URL,
        json={
            "email": user.email,
            "token": token.token,
            "password": "NewStrongPassword123!",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": "Password reset successfully."
    }

    await db_session.refresh(user)

    assert user.verify_password(
        "NewStrongPassword123!"
    )

    token = await db_session.scalar(
        select(PasswordResetTokenModel).where(
            PasswordResetTokenModel.user_id == user.id
        )
    )

    assert token is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reset_password_invalid_token(
    client,
    db_session,
    user_groups,
):
    user = await activate_registered_user(
        client,
        db_session,
    )

    response = await client.post(
        PASSWORD_RESET_COMPLETE_URL,
        json={
            "email": user.email,
            "token": "invalid-token",
            "password": "NewStrongPassword123!",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": "Invalid email or token."
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reset_password_expired_token(
    client,
    db_session,
    user_groups,
):
    user = await activate_registered_user(
        client,
        db_session,
    )

    await client.post(
        PASSWORD_RESET_REQUEST_URL,
        json={
            "email": user.email,
        },
    )

    token = await db_session.scalar(
        select(PasswordResetTokenModel).where(
            PasswordResetTokenModel.user_id == user.id
        )
    )

    token.expires_at = (
        datetime.now(timezone.utc)
        - timedelta(days=1)
    )

    await db_session.commit()

    response = await client.post(
        PASSWORD_RESET_COMPLETE_URL,
        json={
            "email": user.email,
            "token": token.token,
            "password": "NewStrongPassword123!",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": "Invalid email or token."
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_logout_success(
    client,
    db_session,
    user_groups,
):
    user = await activate_registered_user(
        client,
        db_session,
    )

    login_response = await client.post(
        LOGIN_URL,
        json={
            "email": user.email,
            "password": "StrongPassword123!",
        },
    )

    refresh_token = login_response.json()["refresh_token"]

    response = await client.post(
        LOGOUT_URL,
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": "Logged out successfully."
    }

    token = await db_session.scalar(
        select(RefreshTokenModel).where(
            RefreshTokenModel.token == refresh_token
        )
    )

    assert token is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_logout_unknown_token(
    client,
):
    response = await client.post(
        LOGOUT_URL,
        json={
            "refresh_token": "invalid",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Refresh token not found."
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resend_activation_success(
    client,
    db_session,
    user_groups,
):
    await client.post(
        REGISTER_URL,
        json=registration_data(),
    )

    user = await db_session.scalar(
        select(UserModel).where(
            UserModel.email == "user@example.com"
        )
    )

    old_token = await db_session.scalar(
        select(ActivationTokenModel).where(
            ActivationTokenModel.user_id == user.id
        )
    )

    user_id = user.id
    old_token_value = old_token.token

    response = await client.post(
        RESEND_ACTIVATION_URL,
        json={
            "email": user.email,
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": "Activation email sent."
    }

    async with TestingSessionLocal() as session:
        new_token = await session.scalar(
            select(ActivationTokenModel).where(
                ActivationTokenModel.user_id == user_id
            )
        )

    assert new_token is not None
    assert new_token.token != old_token_value


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resend_activation_user_not_found(
    client,
):
    response = await client.post(
        RESEND_ACTIVATION_URL,
        json={
            "email": "missing@example.com",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "User not found."
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resend_activation_user_already_active(
    client,
    db_session,
    user_groups,
):
    user = await activate_registered_user(
        client,
        db_session,
    )

    response = await client.post(
        RESEND_ACTIVATION_URL,
        json={
            "email": user.email,
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": "User already activated."
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_activate_user_not_found(
    admin_client,
):
    response = await admin_client.patch(
        "/api/v1/accounts/admin/users/999/activate/",
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "User not found."
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_activate_user_success(
    admin_client,
    db_session,
    user_groups,
):
    group = await db_session.scalar(
        select(UserGroupModel).where(
            UserGroupModel.name == UserGroupEnum.USER
        )
    )

    user = UserModel.create(
        email="user@test.com",
        raw_password="Password123!",
        group_id=group.id,
    )

    db_session.add(user)

    await db_session.commit()
    await db_session.refresh(user)

    response = await admin_client.patch(
        f"/api/v1/accounts/admin/users/{user.id}/activate/",
    )

    assert response.status_code == 204

    await db_session.refresh(user)

    assert user.is_active is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_user_group_not_found(
    admin_client,
):
    response = await admin_client.patch(
        "/api/v1/accounts/admin/users/999/group/",
        json={
            "group": "moderator",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "User not found."
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_user_group_same_group(
    admin_client,
    db_session,
    user_groups,
):
    group = await db_session.scalar(
        select(UserGroupModel).where(
            UserGroupModel.name == UserGroupEnum.USER
        )
    )

    user = UserModel.create(
        email="user@test.com",
        raw_password="Password123!",
        group_id=group.id,
    )

    user.is_active = True

    db_session.add(user)

    await db_session.commit()

    response = await admin_client.patch(
        f"/api/v1/accounts/admin/users/{user.id}/group/",
        json={
            "group": "user",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": "User already belongs to this group."
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_user_group_success(
    admin_client,
    db_session,
    user_groups,
):
    user_group = await db_session.scalar(
        select(UserGroupModel).where(
            UserGroupModel.name == UserGroupEnum.USER
        )
    )

    moderator_group = await db_session.scalar(
        select(UserGroupModel).where(
            UserGroupModel.name == UserGroupEnum.MODERATOR
        )
    )

    user = UserModel.create(
        email="user@test.com",
        raw_password="Password123!",
        group_id=user_group.id,
    )

    user.is_active = True

    db_session.add(user)

    await db_session.commit()
    await db_session.refresh(user)

    response = await admin_client.patch(
        f"/api/v1/accounts/admin/users/{user.id}/group/",
        json={
            "group": "moderator",
        },
    )

    assert response.status_code == 204

    await db_session.refresh(user)

    assert user.group_id == moderator_group.id

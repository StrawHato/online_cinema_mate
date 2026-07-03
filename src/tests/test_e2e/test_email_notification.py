import asyncio
import re

import pytest


@pytest.mark.asyncio
async def test_user_registration_sends_activation_email(
    client,
    mailhog_client,
    unique_email,
    user_password,
):
    response = await client.post(
        "/accounts/register/",
        json={
            "email": unique_email,
            "password": user_password,
            "password_repeat": user_password,
        },
    )

    assert response.status_code == 201

    await asyncio.sleep(2)

    response = await mailhog_client.get("/messages")

    assert response.status_code == 200

    messages = response.json()["items"]

    message = next(
        (
            msg
            for msg in messages
            if unique_email in str(msg)
        ),
        None,
    )

    assert message is not None
    assert "Account Activation" in str(message)


@pytest.mark.asyncio
async def test_account_activation_sends_completion_email(
    client,
    mailhog_client,
    unique_email,
    user_password,
):
    response = await client.post(
        "/accounts/register/",
        json={
            "email": unique_email,
            "password": user_password,
            "password_repeat": user_password,
        },
    )

    assert response.status_code == 201

    await asyncio.sleep(2)

    response = await mailhog_client.get("/messages")
    messages = response.json()["items"]

    activation_message = next(
        message
        for message in messages
        if unique_email in str(message)
        and "Account Activation" in str(message)
    )

    html = activation_message["Content"]["Body"]

    token = re.search(
        r"/activate/([A-Za-z0-9_\-]+)",
        html,
    ).group(1)

    response = await client.post(
        "/accounts/activate/",
        json={
            "email": unique_email,
            "token": token,
        },
    )

    assert response.status_code == 200

    await asyncio.sleep(2)

    response = await mailhog_client.get("/messages")
    messages = response.json()["items"]

    assert any(
        unique_email in str(message)
        and "Account Activated Successfully" in str(message)
        for message in messages
    )


@pytest.mark.asyncio
async def test_password_reset_request_sends_email(
    client,
    mailhog_client,
    unique_email,
    user_password,
):
    response = await client.post(
        "/accounts/register/",
        json={
            "email": unique_email,
            "password": user_password,
            "password_repeat": user_password,
        },
    )

    assert response.status_code == 201

    await asyncio.sleep(2)

    response = await mailhog_client.get("/messages")
    messages = response.json()["items"]

    activation_message = next(
        message
        for message in messages
        if unique_email in str(message)
        and "Account Activation" in str(message)
    )

    token = re.search(
        r"/activate/([A-Za-z0-9_\-]+)",
        activation_message["Content"]["Body"],
    ).group(1)

    response = await client.post(
        "/accounts/activate/",
        json={
            "email": unique_email,
            "token": token,
        },
    )

    assert response.status_code == 200

    await asyncio.sleep(2)

    response = await client.post(
        "/accounts/password-reset/request/",
        json={
            "email": unique_email,
        },
    )

    assert response.status_code == 200

    await asyncio.sleep(2)

    response = await mailhog_client.get("/messages")
    assert response.status_code == 200

    messages = response.json()["items"]

    assert any(
        unique_email in str(message)
        and "Password Reset Request" in str(message)
        for message in messages
    )


@pytest.mark.asyncio
async def test_password_reset_complete_sends_email(
    client,
    mailhog_client,
    unique_email,
    user_password,
):
    response = await client.post(
        "/accounts/register/",
        json={
            "email": unique_email,
            "password": user_password,
            "password_repeat": user_password,
        },
    )

    assert response.status_code == 201

    await asyncio.sleep(2)

    response = await mailhog_client.get("/messages")
    messages = response.json()["items"]

    activation_message = next(
        message
        for message in messages
        if unique_email in str(message)
        and "Account Activation" in str(message)
    )

    activation_token = re.search(
        r"/activate/([A-Za-z0-9_\-]+)",
        activation_message["Content"]["Body"],
    ).group(1)

    response = await client.post(
        "/accounts/activate/",
        json={
            "email": unique_email,
            "token": activation_token,
        },
    )

    assert response.status_code == 200

    await asyncio.sleep(2)

    response = await client.post(
        "/accounts/password-reset/request/",
        json={
            "email": unique_email,
        },
    )

    assert response.status_code == 200

    await asyncio.sleep(2)

    response = await mailhog_client.get("/messages")
    messages = response.json()["items"]

    reset_message = next(
        message
        for message in messages
        if unique_email in str(message)
        and "Password Reset Request" in str(message)
    )

    reset_token = re.search(
        r"token=([A-Za-z0-9_\-]+)",
        reset_message["Content"]["Body"],
    ).group(1)

    response = await client.post(
        "/accounts/reset-password/complete/",
        json={
            "email": unique_email,
            "token": reset_token,
            "password": "NewPassword123!",
            "password_repeat": "NewPassword123!",
        },
    )

    assert response.status_code == 200

    await asyncio.sleep(2)

    response = await mailhog_client.get("/messages")
    messages = response.json()["items"]

    assert any(
        unique_email in str(message)
        and "Successfully Reset" in str(message)
        for message in messages
    )

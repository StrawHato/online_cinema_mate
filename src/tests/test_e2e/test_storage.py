import asyncio
import re
from io import BytesIO

import aioboto3
import pytest
from PIL import Image

from src.config.settings import get_settings


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_avatar_upload_to_minio(
    client,
    mailhog_client,
    unique_email,
    user_password,
):
    settings = get_settings()

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
        r"token=([A-Za-z0-9_\-]+)",
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

    response = await client.post(
        "/accounts/login/",
        json={
            "email": unique_email,
            "password": user_password,
        },
    )

    assert response.status_code == 201

    access_token = response.json()["access_token"]

    image = Image.new(
        "RGB",
        (100, 100),
        color="red",
    )

    image_bytes = BytesIO()

    image.save(
        image_bytes,
        format="JPEG",
    )

    image_bytes.seek(0)

    response = await client.patch(
        "/profile/",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        files={
            "avatar": (
                "avatar.jpg",
                image_bytes.getvalue(),
                "image/jpeg",
            ),
        },
    )

    assert response.status_code == 200

    profile = response.json()

    avatar_key = profile["avatar"]

    assert avatar_key is not None
    assert avatar_key.startswith("avatars/")
    assert avatar_key.endswith("_avatar.jpg")

    session = aioboto3.Session()

    async with session.client(
        "s3",
        endpoint_url="http://localhost:9000",
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    ) as s3:
        response = await s3.list_objects_v2(
            Bucket=settings.S3_BUCKET_NAME,
            Prefix=avatar_key,
        )

    assert "Contents" in response
    assert len(response["Contents"]) == 1

    uploaded_object = response["Contents"][0]

    assert uploaded_object["Key"] == avatar_key

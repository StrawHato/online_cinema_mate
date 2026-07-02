import pytest
from httpx import AsyncClient

from src.tests.test_integration.test_movies import movie_data


async def create_movie(admin_client: AsyncClient) -> dict:
    response = await admin_client.post(
        "/api/v1/movies/",
        json=movie_data(),
    )

    assert response.status_code == 201

    return response.json()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_empty_cart(
    user_client: AsyncClient,
):
    response = await user_client.get(
        "/api/v1/cart/",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_movies"] == 0
    assert data["total_price"] == "0"
    assert data["items"] == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_movie_to_cart(
    admin_client: AsyncClient,
    user_client: AsyncClient,
):
    movie = await create_movie(admin_client)

    response = await user_client.post(
        f"/api/v1/cart/{movie['uuid']}/",
    )

    assert response.status_code == 204

    response = await user_client.get(
        "/api/v1/cart/",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_movies"] == 1
    assert data["total_price"] == "12.99"

    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["movie"]["uuid"] == movie["uuid"]
    assert item["movie"]["name"] == "Interstellar"
    assert item["movie"]["year"] == 2014
    assert item["movie"]["price"] == "12.99"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_movie_to_cart_twice(
    admin_client: AsyncClient,
    user_client: AsyncClient,
):
    movie = await create_movie(admin_client)

    response = await user_client.post(
        f"/api/v1/cart/{movie['uuid']}/",
    )

    assert response.status_code == 204

    response = await user_client.post(
        f"/api/v1/cart/{movie['uuid']}/",
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Movie is already in cart.",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_remove_movie_from_cart(
    admin_client: AsyncClient,
    user_client: AsyncClient,
):
    movie = await create_movie(admin_client)

    await user_client.post(
        f"/api/v1/cart/{movie['uuid']}/",
    )

    response = await user_client.delete(
        f"/api/v1/cart/{movie['uuid']}/",
    )

    assert response.status_code == 204

    response = await user_client.get(
        "/api/v1/cart/",
    )

    data = response.json()

    assert data["total_movies"] == 0
    assert data["items"] == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_remove_movie_not_in_cart(
    admin_client: AsyncClient,
    user_client: AsyncClient,
):
    movie = await create_movie(admin_client)

    response = await user_client.delete(
        f"/api/v1/cart/{movie['uuid']}/",
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Movie is not in cart.",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_clear_cart(
    admin_client: AsyncClient,
    user_client: AsyncClient,
):
    movie = await create_movie(admin_client)

    await user_client.post(
        f"/api/v1/cart/{movie['uuid']}/",
    )

    response = await user_client.delete(
        "/api/v1/cart/clear/",
    )

    assert response.status_code == 204

    response = await user_client.get(
        "/api/v1/cart/",
    )

    data = response.json()

    assert data["total_movies"] == 0
    assert data["items"] == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_user_cart_as_admin(
    admin_client: AsyncClient,
    user_client: AsyncClient,
    regular_user,
):
    movie = await create_movie(admin_client)

    await user_client.post(
        f"/api/v1/cart/{movie['uuid']}/",
    )

    response = await admin_client.get(
        f"/api/v1/cart/admin/{regular_user.id}/",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_movies"] == 1
    assert data["items"][0]["movie"]["uuid"] == movie["uuid"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_user_cart_not_found(
    admin_client: AsyncClient,
):
    response = await admin_client.get(
        "/api/v1/cart/admin/999/",
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "User not found.",
    }


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,url",
    [
        ("get", "/api/v1/cart/"),
        ("post", "/api/v1/cart/123/"),
        ("delete", "/api/v1/cart/123/"),
        ("delete", "/api/v1/cart/clear/"),
    ],
)
async def test_cart_requires_authentication(
    client: AsyncClient,
    method: str,
    url: str,
):
    response = await getattr(client, method)(url)

    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_cart_creates_cart(
    user_client: AsyncClient,
):
    response = await user_client.get(
        "/api/v1/cart/",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total_movies"] == 0
    assert body["items"] == []

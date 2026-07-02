import pytest
from httpx import AsyncClient

from src.database.models import UserModel
from src.main import app
from src.security.http import get_current_user
from src.tests.test_integration.test_movies import movie_data

MOVIES_URL = "/api/v1/movies/"
ORDERS_URL = "/api/v1/orders/"
CART_URL = "/api/v1/cart/"


async def create_movie(admin_client: AsyncClient) -> dict:
    response = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    assert response.status_code == 201

    return response.json()


async def create_order(
    admin_client: AsyncClient,
    user_client: AsyncClient,
) -> dict:
    movie = await create_movie(admin_client)

    response = await user_client.post(
        f"{CART_URL}{movie['uuid']}/",
    )

    assert response.status_code == 204

    response = await user_client.post(
        ORDERS_URL,
    )

    assert response.status_code == 201

    return response.json()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_order_success(
    admin_client: AsyncClient,
    user_client: AsyncClient,
):
    movie = await create_movie(admin_client)

    await user_client.post(
        f"{CART_URL}{movie['uuid']}/",
    )

    response = await user_client.post(
        ORDERS_URL,
    )

    assert response.status_code == 201

    body = response.json()

    assert body["status"] == "pending"
    assert body["total_amount"] == "12.99"

    assert len(body["items"]) == 1
    assert body["items"][0]["movie"]["uuid"] == movie["uuid"]

    response = await user_client.get(
        CART_URL,
    )

    cart = response.json()

    assert cart["total_movies"] == 0
    assert cart["items"] == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_order_empty_cart(
    user_client: AsyncClient,
):
    response = await user_client.post(
        ORDERS_URL,
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": "Shopping cart is empty.",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_order_pending_conflict(
    admin_client: AsyncClient,
    user_client: AsyncClient,
):
    movie = await create_movie(admin_client)

    await user_client.post(
        f"{CART_URL}{movie['uuid']}/",
    )

    response = await user_client.post(
        ORDERS_URL,
    )

    assert response.status_code == 201

    await user_client.post(
        f"{CART_URL}{movie['uuid']}/",
    )

    response = await user_client.post(
        ORDERS_URL,
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Some movies are already included "
            "in another pending order."
        )
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_orders(
    admin_client: AsyncClient,
    user_client: AsyncClient,
):
    await create_order(
        admin_client,
        user_client,
    )

    response = await user_client.get(
        ORDERS_URL,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert body["total_pages"] == 1
    assert len(body["items"]) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_order(
    admin_client: AsyncClient,
    user_client: AsyncClient,
):
    order = await create_order(
        admin_client,
        user_client,
    )

    response = await user_client.get(
        f"{ORDERS_URL}{order['uuid']}/",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["uuid"] == order["uuid"]
    assert body["status"] == "pending"
    assert body["total_amount"] == "12.99"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_order_not_found(
    user_client: AsyncClient,
):
    response = await user_client.get(
        f"{ORDERS_URL}unknown/",
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Order not found.",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cancel_order(
    admin_client: AsyncClient,
    user_client: AsyncClient,
):
    order = await create_order(
        admin_client,
        user_client,
    )

    response = await user_client.post(
        f"{ORDERS_URL}{order['uuid']}/cancel/",
    )

    assert response.status_code == 204

    response = await user_client.get(
        f"{ORDERS_URL}{order['uuid']}/",
    )

    body = response.json()

    assert body["status"] == "canceled"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cancel_order_twice(
    admin_client: AsyncClient,
    user_client: AsyncClient,
):
    order = await create_order(
        admin_client,
        user_client,
    )

    await user_client.post(
        f"{ORDERS_URL}{order['uuid']}/cancel/",
    )

    response = await user_client.post(
        f"{ORDERS_URL}{order['uuid']}/cancel/",
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": "Order is already canceled.",
    }

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_all_orders_as_admin(
    client: AsyncClient,
    admin_user: UserModel,
    regular_user: UserModel,
):
    app.dependency_overrides[get_current_user] = lambda: admin_user

    movie = await create_movie(client)

    app.dependency_overrides[get_current_user] = lambda: regular_user

    response = await client.post(
        f"{CART_URL}{movie['uuid']}/",
    )
    assert response.status_code == 204

    response = await client.post(
        ORDERS_URL,
    )
    assert response.status_code == 201

    app.dependency_overrides[get_current_user] = lambda: admin_user

    response = await client.get(
        f"{ORDERS_URL}admin/",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert len(body["items"]) == 1

    app.dependency_overrides.pop(
        get_current_user,
        None,
    )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,url",
    [
        ("post", ORDERS_URL),
        ("get", ORDERS_URL),
        ("get", f"{ORDERS_URL}123/"),
        ("post", f"{ORDERS_URL}123/cancel/"),
    ],
)
async def test_orders_require_authentication(
    client: AsyncClient,
    method: str,
    url: str,
):
    response = await getattr(
        client,
        method,
    )(url)

    assert response.status_code == 401
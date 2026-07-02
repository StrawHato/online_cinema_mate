import pytest

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import UserModel
from src.main import app
from src.security.http import get_current_user, get_current_admin
from src.database.models.orders import OrderModel
from src.database.models.payments import (
    PaymentModel,
    PaymentStatusEnum,
)

from src.database.models.orders import OrderStatusEnum

from src.tests.test_integration.test_orders import (
    create_movie,
    create_order,
    CART_URL,
    ORDERS_URL,
)

PAYMENTS_URL = "/api/v1/payments/"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_checkout_success(
    admin_client: AsyncClient,
    user_client: AsyncClient,
    db_session: AsyncSession,
):
    order = await create_order(
        admin_client,
        user_client,
    )

    response = await user_client.post(
        f"{PAYMENTS_URL}{order['uuid']}/checkout/",
    )

    assert response.status_code == 200

    body = response.json()

    assert "checkout_url" in body
    assert body["checkout_url"].startswith("https://")

    db_order = await db_session.scalar(
        select(OrderModel).where(
            OrderModel.uuid == order["uuid"],
        )
    )

    payment = await db_session.scalar(
        select(PaymentModel).where(
            PaymentModel.order_id == db_order.id,
        )
    )

    assert payment is not None
    assert payment.status == PaymentStatusEnum.PENDING


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_checkout_order_not_found(
    user_client: AsyncClient,
):
    response = await user_client.post(
        f"{PAYMENTS_URL}invalid-uuid/checkout/",
    )

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_checkout_already_paid_order(
    admin_client: AsyncClient,
    user_client: AsyncClient,
    db_session: AsyncSession,
):
    order = await create_order(
        admin_client,
        user_client,
    )

    db_order = await db_session.scalar(
        select(OrderModel).where(
            OrderModel.uuid == order["uuid"],
        )
    )

    payment = PaymentModel(
        user_id=db_order.user_id,
        order_id=db_order.id,
        amount=db_order.total_amount,
        status=PaymentStatusEnum.SUCCESSFUL,
    )

    db_session.add(payment)

    db_order.status = OrderStatusEnum.PAID

    await db_session.commit()

    response = await user_client.post(
        f"{PAYMENTS_URL}{order['uuid']}/checkout/",
    )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "Only pending orders can be paid."
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_checkout_existing_pending_payment(
    admin_client: AsyncClient,
    user_client: AsyncClient,
    db_session: AsyncSession,
):
    order = await create_order(
        admin_client,
        user_client,
    )

    response = await user_client.post(
        f"{PAYMENTS_URL}{order['uuid']}/checkout/",
    )

    assert response.status_code == 200

    db_order = await db_session.scalar(
        select(OrderModel).where(
            OrderModel.uuid == order["uuid"],
        )
    )

    payment = await db_session.scalar(
        select(PaymentModel).where(
            PaymentModel.order_id == db_order.id,
        )
    )

    first_uuid = payment.uuid

    response = await user_client.post(
        f"{PAYMENTS_URL}{order['uuid']}/checkout/",
    )

    assert response.status_code == 200

    payment = await db_session.scalar(
        select(PaymentModel).where(
            PaymentModel.order_id == db_order.id,
        )
    )

    assert payment.uuid == first_uuid


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_payment_success(
    admin_client: AsyncClient,
    user_client: AsyncClient,
    db_session: AsyncSession,
):
    order = await create_order(
        admin_client,
        user_client,
    )

    await user_client.post(
        f"{PAYMENTS_URL}{order['uuid']}/checkout/",
    )

    db_order = await db_session.scalar(
        select(OrderModel).where(
            OrderModel.uuid == order["uuid"],
        )
    )

    payment = await db_session.scalar(
        select(PaymentModel).where(
            PaymentModel.order_id == db_order.id,
        )
    )

    response = await user_client.get(
        f"{PAYMENTS_URL}{payment.uuid}/",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["uuid"] == payment.uuid
    assert body["status"] == "pending"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_payment_not_found(
    user_client: AsyncClient,
):
    response = await user_client.get(
        f"{PAYMENTS_URL}invalid-uuid/",
    )

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_payments_success(
    admin_client: AsyncClient,
    user_client: AsyncClient,
):
    order = await create_order(
        admin_client,
        user_client,
    )

    await user_client.post(
        f"{PAYMENTS_URL}{order['uuid']}/checkout/",
    )

    response = await user_client.get(
        PAYMENTS_URL,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["page"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["status"] == "pending"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_all_payments_as_admin(
    client: AsyncClient,
    admin_user: UserModel,
    regular_user: UserModel,
):
    try:
        app.dependency_overrides[
            get_current_user
        ] = lambda: admin_user

        app.dependency_overrides[
            get_current_admin
        ] = lambda: admin_user

        movie = await create_movie(client)

        app.dependency_overrides.pop(
            get_current_admin,
            None,
        )

        app.dependency_overrides[
            get_current_user
        ] = lambda: regular_user

        response = await client.post(
            f"{CART_URL}{movie['uuid']}/",
        )
        assert response.status_code == 204

        response = await client.post(
            ORDERS_URL,
        )
        assert response.status_code == 201

        order = response.json()

        response = await client.post(
            f"{PAYMENTS_URL}{order['uuid']}/checkout/",
        )
        assert response.status_code == 200

        app.dependency_overrides[
            get_current_user
        ] = lambda: admin_user

        app.dependency_overrides[
            get_current_admin
        ] = lambda: admin_user

        response = await client.get(
            f"{PAYMENTS_URL}admin/all/",
        )

        assert response.status_code == 200

        body = response.json()

        assert body["total"] == 1
        assert len(body["items"]) == 1

    finally:
        app.dependency_overrides.pop(
            get_current_user,
            None,
        )
        app.dependency_overrides.pop(
            get_current_admin,
            None,
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refund_success(
    admin_client: AsyncClient,
    user_client: AsyncClient,
    db_session: AsyncSession,
):
    order = await create_order(
        admin_client,
        user_client,
    )

    await user_client.post(
        f"{PAYMENTS_URL}{order['uuid']}/checkout/",
    )

    db_order = await db_session.scalar(
        select(OrderModel).where(
            OrderModel.uuid == order["uuid"],
        )
    )

    payment = await db_session.scalar(
        select(PaymentModel).where(
            PaymentModel.order_id == db_order.id,
        )
    )

    payment.status = PaymentStatusEnum.SUCCESSFUL
    payment.external_payment_id = "pi_test_123"

    db_order.status = OrderStatusEnum.PAID

    await db_session.commit()

    response = await admin_client.post(
        f"{PAYMENTS_URL}{payment.uuid}/refund/",
    )

    assert response.status_code == 204

    await db_session.refresh(payment)

    assert payment.status == PaymentStatusEnum.REFUNDED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refund_already_refunded(
    admin_client: AsyncClient,
    user_client: AsyncClient,
    db_session: AsyncSession,
):
    order = await create_order(
        admin_client,
        user_client,
    )

    await user_client.post(
        f"{PAYMENTS_URL}{order['uuid']}/checkout/",
    )

    db_order = await db_session.scalar(
        select(OrderModel).where(
            OrderModel.uuid == order["uuid"],
        )
    )

    payment = await db_session.scalar(
        select(PaymentModel).where(
            PaymentModel.order_id == db_order.id,
        )
    )

    payment.status = PaymentStatusEnum.REFUNDED

    await db_session.commit()

    response = await admin_client.post(
        f"{PAYMENTS_URL}{payment.uuid}/refund/",
    )

    assert response.status_code == 409


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refund_pending_payment(
    admin_client: AsyncClient,
    user_client: AsyncClient,
    db_session: AsyncSession,
):
    order = await create_order(
        admin_client,
        user_client,
    )

    await user_client.post(
        f"{PAYMENTS_URL}{order['uuid']}/checkout/",
    )

    db_order = await db_session.scalar(
        select(OrderModel).where(
            OrderModel.uuid == order["uuid"],
        )
    )

    payment = await db_session.scalar(
        select(PaymentModel).where(
            PaymentModel.order_id == db_order.id,
        )
    )

    assert payment.status == PaymentStatusEnum.PENDING

    response = await admin_client.post(
        f"{PAYMENTS_URL}{payment.uuid}/refund/",
    )

    assert response.status_code == 409


@pytest.mark.integration
@pytest.mark.asyncio
async def test_payment_success_page(
    client: AsyncClient,
):
    response = await client.get(
        f"{PAYMENTS_URL}success/",
    )

    assert response.status_code == 200

    assert "success" in response.text.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_payment_cancel_page(
    client: AsyncClient,
):
    response = await client.get(
        f"{PAYMENTS_URL}cancel/",
    )

    assert response.status_code == 200

    assert "cancel" in response.text.lower()

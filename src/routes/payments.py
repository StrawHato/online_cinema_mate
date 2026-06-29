from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
    status,
    Query
)

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.payments import PaymentStatusEnum
from src.database.models.accounts import UserModel
from src.database.session import get_db
from src.security.http import get_current_user, get_current_admin
from src.config.dependencies import get_stripe_service
from src.payments.stripe import StripeService
from src.schemas.payments import (
    CheckoutResponseSchema,
    PaymentResponseSchema,
    PaymentListResponseSchema
)
from src.services.payments import PaymentService


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post(
    "/{order_uuid}/checkout/",
    response_model=CheckoutResponseSchema,
)
async def create_checkout_session(
    order_uuid: str,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    stripe_service: StripeService = Depends(get_stripe_service),
) -> CheckoutResponseSchema:

    return await PaymentService.create_checkout_session(
        order_uuid=order_uuid,
        current_user=current_user,
        db=db,
        stripe_service=stripe_service,
    )


@router.post(
    "/webhook/",
    status_code=status.HTTP_200_OK,
)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_service: StripeService = Depends(get_stripe_service),
) -> Response:

    payload = await request.body()

    signature = request.headers.get(
        "Stripe-Signature",
        "",
    )

    await PaymentService.process_webhook(
        payload=payload,
        signature=signature,
        stripe_service=stripe_service,
        db=db,
    )

    return Response(
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/{payment_uuid}/",
    response_model=PaymentResponseSchema,
)
async def get_payment(
    payment_uuid: str,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentResponseSchema:

    return await PaymentService.get_payment(
        payment_uuid=payment_uuid,
        current_user=current_user,
        db=db,
    )


@router.get(
    "/",
    response_model=PaymentListResponseSchema,
)
async def get_payments(
    page: int = Query(
        1,
        ge=1,
    ),
    page_size: int = Query(
        10,
        ge=1,
        le=20,
    ),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentListResponseSchema:

    return await PaymentService.get_payments(
        current_user=current_user,
        db=db,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/admin/all/",
    response_model=PaymentListResponseSchema,
)
async def get_all_payments(
    page: int = Query(
        1,
        ge=1,
    ),
    page_size: int = Query(
        10,
        ge=1,
        le=20,
    ),
    user_id: int | None = Query(
        None,
        ge=1,
    ),
    status: PaymentStatusEnum | None = Query(
        None,
    ),
    created_from: datetime | None = Query(
        None,
    ),
    created_to: datetime | None = Query(
        None,
    ),
    current_user: UserModel = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> PaymentListResponseSchema:

    return await PaymentService.get_all_payments(
        db=db,
        page=page,
        page_size=page_size,
        user_id=user_id,
        status=status,
        created_from=created_from,
        created_to=created_to,
    )

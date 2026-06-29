from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
    status
)

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.accounts import UserModel
from src.database.session import get_db
from src.security.http import get_current_user
from src.config.dependencies import get_stripe_service
from src.payments.stripe import StripeService
from src.schemas.payments import CheckoutResponseSchema
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

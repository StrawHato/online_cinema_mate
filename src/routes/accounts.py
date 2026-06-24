from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.dependencies import (
    get_accounts_email_notificator,
)
from src.database.session import get_db
from src.notifications.interfaces import EmailSenderInterface
from src.schemas.accounts import (
    UserRegistrationRequestSchema,
    UserRegistrationResponseSchema,
)
from src.services.accounts import AccountsService

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post(
    "/register/",
    response_model=UserRegistrationResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user_data: UserRegistrationRequestSchema,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(
        get_accounts_email_notificator
    ),
) -> UserRegistrationResponseSchema:
    return await AccountsService.register(
        user_data=user_data,
        db=db,
        email_sender=email_sender,
    )

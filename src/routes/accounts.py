from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.accounts import UserModel
from src.security.http import get_current_user
from src.config.dependencies import (
    get_accounts_email_notificator,
    get_jwt_auth_manager,
)
from src.config.settings import Settings, get_settings
from src.database.session import get_db
from src.notifications.interfaces import EmailSenderInterface
from src.schemas.accounts import (
    MessageResponseSchema,
    PasswordResetCompleteRequestSchema,
    PasswordResetRequestSchema,
    TokenRefreshRequestSchema,
    TokenRefreshResponseSchema,
    UserActivationRequestSchema,
    UserLoginRequestSchema,
    UserLoginResponseSchema,
    UserRegistrationRequestSchema,
    UserRegistrationResponseSchema,
    ChangePasswordRequestSchema,
    LogoutRequestSchema,
    ResendActivationRequestSchema,
)
from src.security.interfaces import JWTAuthManagerInterface
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
) -> UserRegistrationResponseSchema:
    return await AccountsService.register(
        user_data=user_data,
        db=db,
    )


@router.post(
    "/activate/",
    response_model=MessageResponseSchema,
)
async def activate_account(
    activation_data: UserActivationRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema:
    return await AccountsService.activate(
        activation_data=activation_data,
        db=db
    )


@router.post(
    "/password-reset/request/",
    response_model=MessageResponseSchema,
)
async def request_password_reset_token(
    data: PasswordResetRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema:
    return await AccountsService.request_password_reset(
        data=data,
        db=db,
    )


@router.post(
    "/reset-password/complete/",
    response_model=MessageResponseSchema,
)
async def reset_password(
    data: PasswordResetCompleteRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> MessageResponseSchema:
    return await AccountsService.reset_password(
        data=data,
        db=db,
    )


@router.post(
    "/login/",
    response_model=UserLoginResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def login_user(
    login_data: UserLoginRequestSchema,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    jwt_manager: JWTAuthManagerInterface = Depends(
        get_jwt_auth_manager
    ),
) -> UserLoginResponseSchema:
    return await AccountsService.login(
        login_data=login_data,
        db=db,
        settings=settings,
        jwt_manager=jwt_manager,
    )


@router.post(
    "/refresh/",
    response_model=TokenRefreshResponseSchema,
)
async def refresh_access_token(
    token_data: TokenRefreshRequestSchema,
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(
        get_jwt_auth_manager
    ),
) -> TokenRefreshResponseSchema:
    return await AccountsService.refresh_access_token(
        token_data=token_data,
        db=db,
        jwt_manager=jwt_manager,
    )


@router.post(
    "/change-password/",
    response_model=MessageResponseSchema,
)
async def change_password(
    data: ChangePasswordRequestSchema,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AccountsService.change_password(
        user_id=current_user.id,
        data=data,
        db=db,
    )


@router.post(
    "/logout/",
    response_model=MessageResponseSchema,
)
async def logout(
    data: LogoutRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    return await AccountsService.logout(
        token_data=data,
        db=db,
    )


@router.post(
    "/activation/resend/",
    response_model=MessageResponseSchema,
)
async def resend_activation_token(
    data: ResendActivationRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    return await AccountsService.resend_activation_token(
        data=data,
        db=db,
    )

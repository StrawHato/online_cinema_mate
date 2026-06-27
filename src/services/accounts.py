from datetime import datetime, timezone
from typing import cast

from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database.models.accounts import (
    UserModel,
    UserGroupModel,
    UserGroupEnum,
    ActivationTokenModel,
    PasswordResetTokenModel,
    RefreshTokenModel,
    UserProfileModel,
)
from src.config.settings import Settings
from src.exceptions import BaseSecurityError
from src.schemas.accounts import (
    UserRegistrationRequestSchema,
    UserRegistrationResponseSchema,
    MessageResponseSchema,
    UserActivationRequestSchema,
    PasswordResetRequestSchema,
    PasswordResetCompleteRequestSchema,
    UserLoginRequestSchema,
    UserLoginResponseSchema,
    TokenRefreshRequestSchema,
    TokenRefreshResponseSchema,
    ChangePasswordRequestSchema,
    LogoutRequestSchema,
    ResendActivationRequestSchema,
)
from src.tasks.emails import (
    send_activation_email_task, send_activation_complete_email_task, send_password_reset_email_task,
    send_password_reset_complete_email_task
)
from src.security.interfaces import JWTAuthManagerInterface


class AccountsService:

    @staticmethod
    async def _get_user_or_404(
            user_id: int,
            db: AsyncSession,
    ) -> UserModel:

        stmt = (
            select(UserModel)
            .where(
                UserModel.id == user_id,
            )
        )

        result = await db.execute(stmt)

        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        return user

    @staticmethod
    async def register(
        user_data: UserRegistrationRequestSchema,
        db: AsyncSession,
    ) -> UserRegistrationResponseSchema:

        stmt = select(UserModel).where(UserModel.email == user_data.email)
        result = await db.execute(stmt)
        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A user with this email {user_data.email} already exists."
            )

        stmt = select(UserGroupModel).where(
            UserGroupModel.name == UserGroupEnum.USER
        )
        result = await db.execute(stmt)
        user_group = result.scalars().first()

        if not user_group:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Default user group not found."
            )

        try:
            new_user = UserModel.create(
                email=str(user_data.email),
                raw_password=user_data.password,
                group_id=user_group.id,
            )

            db.add(new_user)
            await db.flush()

            activation_token = ActivationTokenModel(
                user_id=new_user.id
            )
            db.add(activation_token)

            profile = UserProfileModel(
                user=new_user,
            )
            db.add(profile)

            await db.commit()
            await db.refresh(new_user)

        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during user creation."
            ) from e

        activation_link = (
            f"http://127.0.0.1:8000/api/v1/accounts/activate/"
            f"{activation_token.token}"
        )

        send_activation_email_task.delay(
            new_user.email,
            activation_link,
        )

        return UserRegistrationResponseSchema.model_validate(new_user)

    @staticmethod
    async def activate(
            activation_data: UserActivationRequestSchema,
            db: AsyncSession,
    ) -> MessageResponseSchema:

        stmt = (
            select(ActivationTokenModel)
            .options(joinedload(ActivationTokenModel.user))
            .join(UserModel)
            .where(
                UserModel.email == activation_data.email,
                ActivationTokenModel.token == activation_data.token,
            )
        )

        result = await db.execute(stmt)
        token_record = result.scalars().first()

        now_utc = datetime.now(timezone.utc)

        if (
                not token_record
                or cast(datetime, token_record.expires_at).replace(
            tzinfo=timezone.utc
        ) < now_utc
        ):
            if token_record:
                await db.delete(token_record)
                await db.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired activation token.",
            )

        user = token_record.user

        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is already active.",
            )

        user.is_active = True

        await db.delete(token_record)
        await db.commit()

        login_link = "http://127.0.0.1/api/v1/accounts/login/"

        send_activation_complete_email_task.delay(
            str(activation_data.email),
            login_link,
        )

        return MessageResponseSchema(
            message="User account activated successfully."
        )

    @staticmethod
    async def request_password_reset(
            data: PasswordResetRequestSchema,
            db: AsyncSession,
    ) -> MessageResponseSchema:

        stmt = select(UserModel).filter_by(email=data.email)
        result = await db.execute(stmt)

        user = result.scalars().first()

        if not user or not user.is_active:
            return MessageResponseSchema(
                message=(
                    "If you are registered, "
                    "you will receive an email with instructions."
                )
            )

        await db.execute(
            delete(PasswordResetTokenModel).where(
                PasswordResetTokenModel.user_id == user.id
            )
        )

        reset_token = PasswordResetTokenModel(
            user_id=cast(int, user.id)
        )

        db.add(reset_token)

        await db.commit()

        reset_link = (
            f"http://127.0.0.1:8000/api/v1/accounts/reset-password/complete/"
            f"?token={reset_token.token}"
        )

        send_password_reset_email_task.delay(
            str(data.email),
            reset_link,
        )

        return MessageResponseSchema(
            message=(
                "If you are registered, "
                "you will receive an email with instructions."
            )
        )

    @staticmethod
    async def reset_password(
            data: PasswordResetCompleteRequestSchema,
            db: AsyncSession,
    ) -> MessageResponseSchema:

        stmt = select(UserModel).filter_by(email=data.email)

        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or token.",
            )

        stmt = select(PasswordResetTokenModel).filter_by(
            user_id=user.id
        )

        result = await db.execute(stmt)
        token_record = result.scalars().first()

        if not token_record or token_record.token != data.token:
            if token_record:
                await db.delete(token_record)
                await db.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or token.",
            )

        expires_at = cast(
            datetime,
            token_record.expires_at
        ).replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            await db.delete(token_record)
            await db.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or token.",
            )

        try:
            user.password = data.password

            await db.delete(token_record)

            await db.commit()

        except SQLAlchemyError:
            await db.rollback()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "An error occurred while resetting the password."
                ),
            )

        login_link = "http://127.0.0.1:8000/api/v1/accounts/login/"

        send_password_reset_complete_email_task.delay(
            str(data.email),
            login_link,
        )

        return MessageResponseSchema(
            message="Password reset successfully."
        )

    @staticmethod
    async def login(
            login_data: UserLoginRequestSchema,
            db: AsyncSession,
            settings: Settings,
            jwt_manager: JWTAuthManagerInterface,
    ) -> UserLoginResponseSchema:

        stmt = select(UserModel).filter_by(
            email=login_data.email
        )

        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user or not user.verify_password(
                login_data.password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not activated.",
            )

        jwt_refresh_token = jwt_manager.create_refresh_token(
            {"user_id": user.id}
        )

        try:
            refresh_token = RefreshTokenModel.create(
                user_id=user.id,
                days_valid=settings.LOGIN_TIME_DAYS,
                token=jwt_refresh_token,
            )

            db.add(refresh_token)

            await db.flush()
            await db.commit()

        except SQLAlchemyError:
            await db.rollback()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "An error occurred while processing the request."
                ),
            )

        jwt_access_token = jwt_manager.create_access_token(
            {"user_id": user.id}
        )

        return UserLoginResponseSchema(
            access_token=jwt_access_token,
            refresh_token=jwt_refresh_token,
        )

    @staticmethod
    async def refresh_access_token(
            token_data: TokenRefreshRequestSchema,
            db: AsyncSession,
            jwt_manager: JWTAuthManagerInterface,
    ) -> TokenRefreshResponseSchema:

        try:
            decoded_token = jwt_manager.decode_refresh_token(
                token_data.refresh_token
            )

            user_id = decoded_token.get("user_id")

        except BaseSecurityError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            )

        stmt = select(RefreshTokenModel).filter_by(
            token=token_data.refresh_token
        )

        result = await db.execute(stmt)

        refresh_token_record = result.scalars().first()

        if not refresh_token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found.",
            )

        user = await AccountsService._get_user_or_404(user_id, db)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not activated.",
            )

        new_access_token = jwt_manager.create_access_token(
            {"user_id": user_id}
        )

        return TokenRefreshResponseSchema(
            access_token=new_access_token
        )

    @staticmethod
    async def change_password(
            user_id: int,
            data: ChangePasswordRequestSchema,
            db: AsyncSession,
    ) -> MessageResponseSchema:

        user = await AccountsService._get_user_or_404(user_id, db)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

        if not user.verify_password(data.old_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Old password is incorrect."
            )

        user.password = data.new_password

        await db.commit()

        return MessageResponseSchema(
            message="Password changed successfully."
        )

    @staticmethod
    async def logout(
            token_data: LogoutRequestSchema,
            db: AsyncSession,
    ) -> MessageResponseSchema:

        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.token == token_data.refresh_token
        )

        result = await db.execute(stmt)

        refresh_token = result.scalar_one_or_none()

        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refresh token not found."
            )

        await db.delete(refresh_token)

        await db.commit()

        return MessageResponseSchema(
            message="Logged out successfully."
        )

    @staticmethod
    async def resend_activation_token(
            data: ResendActivationRequestSchema,
            db: AsyncSession,
    ) -> MessageResponseSchema:

        stmt = select(UserModel).where(
            UserModel.email == data.email
        )

        result = await db.execute(stmt)

        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already activated."
            )

        await db.execute(
            delete(ActivationTokenModel).where(
                ActivationTokenModel.user_id == user.id
            )
        )

        activation_token = ActivationTokenModel(
            user_id=user.id
        )

        db.add(activation_token)

        await db.commit()
        await db.refresh(activation_token)

        activation_link = (
            f"http://127.0.0.1:8000/accounts/activate/"
            f"{activation_token.token}"
        )

        send_activation_email_task.delay(
            user.email,
            activation_link,
        )

        return MessageResponseSchema(
            message="Activation email sent."
        )

    @staticmethod
    async def activate_user(
            user_id: int,
            db: AsyncSession,
    ) -> None:
        user = await AccountsService._get_user_or_404(user_id=user_id, db=db)

        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already activated.",
            )

        user.is_active = True

        await db.commit()

    @staticmethod
    async def update_user_group(
            user_id: int,
            group: UserGroupEnum,
            db: AsyncSession,
    ) -> None:
        user = await AccountsService._get_user_or_404(
            user_id=user_id,
            db=db,
        )

        stmt = (
            select(UserGroupModel)
            .where(
                UserGroupModel.name == group,
            )
        )

        result = await db.execute(stmt)

        user_group = result.scalar_one_or_none()

        if user_group is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found.",
            )

        if user.group_id == user_group.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already belongs to this group.",
            )

        user.group = user_group

        await db.commit()

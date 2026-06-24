from datetime import datetime, timezone
from typing import cast

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database.models.accounts import (
    UserModel,
    UserGroupModel,
    UserGroupEnum,
    ActivationTokenModel,
)
from src.schemas.accounts import (
    UserRegistrationRequestSchema,
    UserRegistrationResponseSchema,
    MessageResponseSchema,
    UserActivationRequestSchema,
)
from src.notifications.interfaces import EmailSenderInterface


class AccountsService:
    @staticmethod
    async def register(
        user_data: UserRegistrationRequestSchema,
        db: AsyncSession,
        email_sender: EmailSenderInterface,
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

            await db.commit()
            await db.refresh(new_user)

        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during user creation."
            ) from e

        activation_link = "http://127.0.0.1/accounts/activate/"

        await email_sender.send_activation_email(
            new_user.email,
            activation_link
        )

        return UserRegistrationResponseSchema.model_validate(new_user)

    @staticmethod
    async def activate(
            activation_data: UserActivationRequestSchema,
            db: AsyncSession,
            email_sender: EmailSenderInterface,
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

        login_link = "http://127.0.0.1/accounts/login/"

        await email_sender.send_activation_complete_email(
            str(activation_data.email),
            login_link,
        )

        return MessageResponseSchema(
            message="User account activated successfully."
        )

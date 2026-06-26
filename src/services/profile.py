from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.accounts import UserModel
from src.schemas.profile import (
    ProfileUpdateRequestSchema,
    ProfileResponseSchema,
)
from src.storages.interfaces import StorageInterface


class ProfileService:
    @staticmethod
    async def get_profile(
        current_user: UserModel,
    ) -> ProfileResponseSchema:
        profile = current_user.profile

        return ProfileResponseSchema.model_validate(profile)

    @staticmethod
    async def update_profile(
            db: AsyncSession,
            storage: StorageInterface,
            current_user: UserModel,
            profile_data: ProfileUpdateRequestSchema,
    ) -> ProfileResponseSchema:
        profile = current_user.profile

        data = profile_data.model_dump(
            exclude_unset=True,
            exclude={"avatar"},
        )

        for field, value in data.items():
            setattr(profile, field, value)

        if profile_data.avatar is not None:
            avatar_bytes = await profile_data.avatar.read()

            avatar_key = (
                f"avatars/"
                f"{current_user.id}_"
                f"{profile_data.avatar.filename}"
            )

            await storage.upload_file(
                file_name=avatar_key,
                file_data=avatar_bytes,
                content_type=profile_data.avatar.content_type
                             or "application/octet-stream",
            )

            profile.avatar = avatar_key

        await db.commit()
        await db.refresh(profile)

        return ProfileResponseSchema.model_validate(profile)

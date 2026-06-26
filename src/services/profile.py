from src.database.models.accounts import UserModel
from src.schemas.profile import (
    ProfileResponseSchema,
)


class ProfileService:
    @staticmethod
    async def get_profile(
        current_user: UserModel,
    ) -> ProfileResponseSchema:
        profile = current_user.profile

        return ProfileResponseSchema.model_validate(profile)

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.accounts import UserModel
from src.database.session import get_db
from src.config.dependencies import get_storage
from src.schemas.profile import (
    ProfileResponseSchema,
    ProfileUpdateRequestSchema,
)
from src.security.http import get_current_user
from src.services.profile import ProfileService
from src.storages.interfaces import StorageInterface


router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
)


@router.get(
    "/",
    response_model=ProfileResponseSchema,
    summary="Get current user profile",
    status_code=status.HTTP_200_OK,
)
async def get_profile(
    current_user: UserModel = Depends(get_current_user),
) -> ProfileResponseSchema:
    return await ProfileService.get_profile(
        current_user=current_user,
    )


@router.patch(
    "/",
    response_model=ProfileResponseSchema,
    summary="Update current user profile",
    status_code=status.HTTP_200_OK,
)
async def update_profile(
    profile_data: ProfileUpdateRequestSchema = Depends(
        ProfileUpdateRequestSchema.from_form
    ),
    db: AsyncSession = Depends(get_db),
    storage: StorageInterface = Depends(get_storage),
    current_user: UserModel = Depends(get_current_user),
) -> ProfileResponseSchema:
    return await ProfileService.update_profile(
        db=db,
        storage=storage,
        current_user=current_user,
        profile_data=profile_data,
    )

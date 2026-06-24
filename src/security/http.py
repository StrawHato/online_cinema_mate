from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.database.models.accounts import UserModel
from src.database.session import get_db
from src.config.dependencies import get_jwt_auth_manager
from src.security.interfaces import JWTAuthManagerInterface
from src.exceptions import BaseSecurityError

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(
        get_jwt_auth_manager
    ),
) -> UserModel:

    token = credentials.credentials

    try:
        payload = jwt_manager.decode_access_token(
            token
        )

        user_id = payload.get("user_id")

    except BaseSecurityError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        )

    stmt = select(UserModel).where(
        UserModel.id == user_id
    )

    result = await db.execute(stmt)

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not activated.",
        )

    return user

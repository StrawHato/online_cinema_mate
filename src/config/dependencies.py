from functools import lru_cache

from src.config.settings import get_settings
from src.security.interfaces import JWTAuthManagerInterface
from src.security.token_manager import JWTAuthManager


@lru_cache
def get_jwt_auth_manager() -> JWTAuthManagerInterface:
    settings = get_settings()

    return JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
    )

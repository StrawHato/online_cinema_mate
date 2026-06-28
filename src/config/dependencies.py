from functools import lru_cache

from fastapi import Depends

from src.notifications import EmailSenderInterface
from src.notifications.emails import EmailSender
from src.config.settings import get_settings, Settings
from src.security.interfaces import JWTAuthManagerInterface
from src.security.token_manager import JWTAuthManager
from src.storages.interfaces import StorageInterface
from src.storages.s3 import S3Storage
from src.payments.stripe import StripeService


@lru_cache
def get_jwt_auth_manager() -> JWTAuthManagerInterface:
    settings = get_settings()

    return JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
    )


@lru_cache
def get_accounts_email_notificator() -> EmailSenderInterface:
    settings = get_settings()

    return EmailSender(
        hostname=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        email=settings.EMAIL_HOST_USER,
        password=settings.EMAIL_HOST_PASSWORD,
        use_tls=settings.EMAIL_USE_TLS,
        template_dir=settings.PATH_TO_EMAIL_TEMPLATES_DIR,
        activation_email_template_name=settings.ACTIVATION_EMAIL_TEMPLATE_NAME,
        activation_complete_email_template_name=settings.ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME,
        password_email_template_name=settings.PASSWORD_RESET_TEMPLATE_NAME,
        password_complete_email_template_name=settings.PASSWORD_RESET_COMPLETE_TEMPLATE_NAME,
    )


def get_storage(
    settings: Settings = Depends(get_settings),
) -> StorageInterface:
    return S3Storage(
        endpoint_url=settings.S3_ENDPOINT,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        bucket_name=settings.S3_BUCKET_NAME,
    )


@lru_cache
def get_stripe_service() -> StripeService:
    settings = get_settings()

    return StripeService(
        secret_key=settings.STRIPE_SECRET_KEY,
    )

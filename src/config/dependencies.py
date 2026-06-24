from functools import lru_cache

from src.notifications import EmailSenderInterface
from src.notifications.emails import EmailSender
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

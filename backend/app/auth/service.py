from app.core.config import settings


def is_email_allowed(email: str) -> bool:
    """Single-user allowlist: fail closed if ALLOWED_EMAIL isn't configured."""
    return bool(settings.allowed_email) and email.lower() == settings.allowed_email.lower()

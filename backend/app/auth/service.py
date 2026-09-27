from app.core.config import settings


def is_email_allowed(email: str) -> bool:
    """Shared allowlist: fails closed, since an unset value parses to an empty set."""
    return email.lower() in settings.allowed_email_set

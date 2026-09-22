from typing import ClassVar

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 32 chars is what both documented generators produce at minimum
# (`openssl rand -hex 32` → 64, `secrets.token_urlsafe(32)` → 43).
MIN_SESSION_SECRET_LENGTH = 32


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/carstats.db"
    uploads_dir: str = "./data/uploads"
    frontend_dist_dir: str = "../frontend/dist"

    session_secret: str = ""

    google_client_id: str = ""
    google_client_secret: str = ""
    oauth_redirect_url: str = "http://localhost:8000/auth/callback"

    allowed_email: str = ""

    # Unset, the Secure flag follows oauth_redirect_url's scheme: https in
    # production, http for local dev where a Secure cookie never comes back.
    cookie_secure: bool | None = None

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", env_prefix="CARSTATS_"
    )

    @property
    def session_cookie_secure(self) -> bool:
        if self.cookie_secure is not None:
            return self.cookie_secure
        return self.oauth_redirect_url.lower().startswith("https://")

    @model_validator(mode="after")
    def _require_session_secret(self) -> "Settings":
        if len(self.session_secret) < MIN_SESSION_SECRET_LENGTH:
            raise ValueError(
                "CARSTATS_SESSION_SECRET must be set to a random value of at least "
                + f"{MIN_SESSION_SECRET_LENGTH} characters "
                + "(generate via `openssl rand -hex 32`)"
            )
        return self


settings = Settings()

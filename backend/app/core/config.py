from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/carstats.db"
    uploads_dir: str = "./data/uploads"
    frontend_dist_dir: str = "../frontend/dist"

    session_secret: str = "dev-secret-change-me"

    google_client_id: str = ""
    google_client_secret: str = ""
    oauth_redirect_url: str = "http://localhost:8000/auth/callback"

    allowed_email: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="CARSTATS_")


settings = Settings()

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import ValidationError
from starlette.middleware.sessions import SessionMiddleware

from app.auth.service import is_email_allowed
from app.core.config import Settings, settings
from app.main import SESSION_MAX_AGE_SECONDS


def test_unauthenticated_request_is_rejected(anon_client):
    response = anon_client.get("/api/car")
    assert response.status_code == 401


def test_authenticated_request_succeeds(client):
    response = client.get("/api/car")
    assert response.status_code == 200


def test_auth_me_requires_session(anon_client):
    assert anon_client.get("/auth/me").status_code == 401


def test_is_email_allowed_matches_case_insensitively(monkeypatch):
    monkeypatch.setattr(settings, "allowed_email", "me@example.com")
    assert is_email_allowed("me@example.com")
    assert is_email_allowed("ME@EXAMPLE.COM")
    assert not is_email_allowed("someoneelse@example.com")


def test_is_email_allowed_fails_closed_when_unconfigured(monkeypatch):
    monkeypatch.setattr(settings, "allowed_email", "")
    assert not is_email_allowed("anyone@example.com")


# _env_file=None keeps these off the developer's own backend/.env.
def test_settings_rejects_missing_session_secret(monkeypatch):
    monkeypatch.delenv("CARSTATS_SESSION_SECRET", raising=False)
    with pytest.raises(ValidationError, match="CARSTATS_SESSION_SECRET"):
        Settings(_env_file=None)


@pytest.mark.parametrize("secret", ["", "short-secret"])
def test_settings_rejects_weak_session_secret(monkeypatch, secret):
    monkeypatch.setenv("CARSTATS_SESSION_SECRET", secret)
    with pytest.raises(ValidationError, match="CARSTATS_SESSION_SECRET"):
        Settings(_env_file=None)


def test_settings_accepts_real_session_secret(monkeypatch):
    monkeypatch.setenv("CARSTATS_SESSION_SECRET", "3f7a" * 16)
    assert Settings(_env_file=None).session_secret == "3f7a" * 16


def test_cookie_secure_defaults_to_redirect_url_scheme():
    https = Settings(
        _env_file=None,
        session_secret="3f7a" * 16,
        oauth_redirect_url="https://carstats.example.com/auth/callback",
    )
    http = Settings(
        _env_file=None,
        session_secret="3f7a" * 16,
        oauth_redirect_url="http://localhost:8000/auth/callback",
    )
    assert https.session_cookie_secure
    assert not http.session_cookie_secure


@pytest.mark.parametrize("override", [True, False])
def test_cookie_secure_override_wins_over_scheme(override):
    config = Settings(
        _env_file=None,
        session_secret="3f7a" * 16,
        oauth_redirect_url="http://localhost:8000/auth/callback",
        cookie_secure=override,
    )
    assert config.session_cookie_secure is override


def test_session_cookie_carries_hardening_flags(monkeypatch):
    monkeypatch.setattr(settings, "cookie_secure", True)
    # SessionMiddleware reads the flags once, at construction time.
    app = FastAPI()
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        same_site="lax",
        https_only=settings.session_cookie_secure,
        max_age=SESSION_MAX_AGE_SECONDS,
    )

    @app.get("/sign-in")
    async def sign_in(request: Request) -> dict[str, str]:
        request.session["user_email"] = "me@example.com"
        return {"ok": "1"}

    cookie = TestClient(app, base_url="https://testserver").get("/sign-in").headers[
        "set-cookie"
    ]
    assert "secure" in cookie
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert f"Max-Age={SESSION_MAX_AGE_SECONDS}" in cookie

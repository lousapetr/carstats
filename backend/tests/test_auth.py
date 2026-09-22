import pytest
from pydantic import ValidationError

from app.auth.service import is_email_allowed
from app.core.config import Settings, settings


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

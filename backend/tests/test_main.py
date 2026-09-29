import os

import pytest

from app.core.config import settings


def test_unknown_api_path_404s_with_json(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.json()["detail"] == "Not found"


def test_unknown_auth_path_404s(client):
    assert client.get("/auth/does-not-exist").status_code == 404


def test_client_side_route_falls_back_to_the_spa(client):
    """Only meaningful once the frontend has been built; without a dist dir
    the catch-all is not registered and FastAPI 404s instead.
    """
    response = client.get("/fuel")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        assert "<!doctype html" in response.text.lower()


def _dist_dir():
    """The catch-all and the /assets mount only exist when the frontend has
    been built, so the cache-header tests skip on a backend-only checkout.
    """
    if not os.path.isdir(settings.frontend_dist_dir):
        pytest.skip("frontend not built")
    return os.path.abspath(settings.frontend_dist_dir)


def test_hashed_assets_are_cached_forever(client):
    assets = os.path.join(_dist_dir(), "assets")
    name = next(f for f in sorted(os.listdir(assets)) if f.endswith((".js", ".css")))

    response = client.get(f"/assets/{name}")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"


def test_dist_root_files_are_revalidated(client):
    """sw.js keeps its name across builds, so a cached copy that isn't
    revalidated keeps serving the previous deploy's precache.
    """
    _dist_dir()
    response = client.get("/sw.js")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-cache"


def test_spa_fallback_is_revalidated(client):
    _dist_dir()
    response = client.get("/fuel")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-cache"

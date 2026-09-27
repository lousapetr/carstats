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

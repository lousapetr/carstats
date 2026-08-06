def test_get_car_profile_defaults(client):
    profile = client.get("/api/car").json()
    assert profile["name"] == ""
    assert profile["make"] == ""
    assert profile["current_mileage_km"] == 0


def test_update_car_profile(client):
    response = client.put(
        "/api/car",
        json={"name": "Škodovka", "make": "Škoda", "model": "Octavia", "year": 2018},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Škodovka"
    assert body["make"] == "Škoda"
    assert body["model"] == "Octavia"
    assert body["year"] == 2018

    profile = client.get("/api/car").json()
    assert profile["name"] == "Škodovka"

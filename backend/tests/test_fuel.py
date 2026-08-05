def test_create_fuel_entry_updates_car_mileage(client):
    response = client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_total": 60},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["price_per_liter"] == 1.5
    assert body["consumption_l_per_100km"] is None

    car = client.get("/api/car").json()
    assert car["current_mileage_km"] == 10000


def test_consumption_computed_from_previous_entry(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_total": 60},
    )
    second = client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-05", "mileage_km": 10500, "liters": 35, "price_total": 55},
    ).json()
    assert second["consumption_l_per_100km"] == 7.0


def test_list_fuel_entries_newest_first(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_total": 60},
    )
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-05", "mileage_km": 10500, "liters": 35, "price_total": 55},
    )
    entries = client.get("/api/fuel-entries").json()
    assert [e["mileage_km"] for e in entries] == [10500, 10000]


def test_delete_fuel_entry(client):
    created = client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_total": 60},
    ).json()
    response = client.delete(f"/api/fuel-entries/{created['id']}")
    assert response.status_code == 204
    assert client.get("/api/fuel-entries").json() == []


def test_delete_missing_fuel_entry_404s(client):
    response = client.delete("/api/fuel-entries/999")
    assert response.status_code == 404

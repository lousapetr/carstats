def test_create_service_entry_updates_car_mileage(client):
    response = client.post(
        "/api/service-entries",
        json={"date": "2026-08-02", "mileage_km": 10200, "type": "oil_change", "cost": 80},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "oil_change"
    assert body["attachments"] == []

    car = client.get("/api/car").json()
    assert car["current_mileage_km"] == 10200


def test_list_service_entries_ordered_by_date_desc(client):
    client.post(
        "/api/service-entries",
        json={"date": "2026-01-01", "mileage_km": 9000, "type": "tires", "cost": 400},
    )
    client.post(
        "/api/service-entries",
        json={"date": "2026-08-02", "mileage_km": 10200, "type": "oil_change", "cost": 80},
    )
    entries = client.get("/api/service-entries").json()
    assert [e["type"] for e in entries] == ["oil_change", "tires"]


def test_delete_service_entry(client):
    created = client.post(
        "/api/service-entries",
        json={"date": "2026-08-02", "mileage_km": 10200, "type": "oil_change", "cost": 80},
    ).json()
    response = client.delete(f"/api/service-entries/{created['id']}")
    assert response.status_code == 204
    assert client.get("/api/service-entries").json() == []

import pytest


def test_create_service_entry_updates_car_mileage(client):
    response = client.post(
        "/api/service-entries",
        json={"date": "2026-08-02", "mileage_km": 10200, "type": "oil_change", "cost": 80},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "oil_change"
    assert body["cost_czk"] == 80.0
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


def test_update_service_entry(client):
    created = client.post(
        "/api/service-entries",
        json={"date": "2026-08-02", "mileage_km": 10200, "type": "oil_change", "cost": 80},
    ).json()

    updated = client.put(
        f"/api/service-entries/{created['id']}",
        json={"date": "2026-08-02", "mileage_km": 10200, "type": "tires", "cost": 90},
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["type"] == "tires"
    assert body["cost_czk"] == 90.0


def test_update_missing_service_entry_404s(client):
    response = client.put(
        "/api/service-entries/999",
        json={"date": "2026-08-02", "mileage_km": 10200, "type": "oil_change", "cost": 80},
    )
    assert response.status_code == 404


def test_create_service_entry_with_lower_mileage_than_history_is_rejected(client):
    client.post(
        "/api/service-entries",
        json={"date": "2026-08-05", "mileage_km": 10500, "type": "oil_change", "cost": 80},
    )
    response = client.post(
        "/api/service-entries",
        json={"date": "2026-08-10", "mileage_km": 10200, "type": "tires", "cost": 400},
    )
    assert response.status_code == 400


def test_create_service_entry_with_eur_converts_to_czk(client):
    response = client.post(
        "/api/service-entries",
        json={
            "date": "2026-08-02",
            "mileage_km": 10200,
            "type": "oil_change",
            "cost": 50,
            "currency": "EUR",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["cost"] == 50.0
    assert body["cost_czk"] == 1250.0


@pytest.mark.parametrize(
    "override",
    [
        {"cost": -1},
        {"mileage_km": -1},
        {"description": "x" * 1001},
        {"notes": "x" * 1001},
    ],
)
def test_create_service_entry_rejects_out_of_range_values(client, override):
    payload = {"date": "2026-08-02", "mileage_km": 10200, "type": "oil_change", "cost": 80}
    response = client.post("/api/service-entries", json=payload | override)
    assert response.status_code == 422
    assert client.get("/api/service-entries").json() == []


def test_same_day_service_entries_are_ordered_by_mileage(client):
    for mileage_km in (10300, 10000, 10100):
        response = client.post(
            "/api/service-entries",
            json={"date": "2026-08-22", "mileage_km": mileage_km, "type": "other", "cost": 10},
        )
        assert response.status_code == 201, response.text

    entries = client.get("/api/service-entries").json()
    assert [e["mileage_km"] for e in entries] == [10300, 10100, 10000]


SERVICE = {
    "date": "2026-08-02",
    "mileage_km": 10200,
    "type": "oil_change",
    "description": "Oil and filter",
    "cost": 80,
}


def test_duplicate_service_entry_ignores_case_and_whitespace(client):
    client.post("/api/service-entries", json=SERVICE)
    response = client.post(
        "/api/service-entries", json={**SERVICE, "description": "  oil   AND filter "}
    )
    assert response.status_code == 409
    assert "už existuje" in response.json()["detail"]


def test_duplicate_service_entry_with_missing_descriptions(client):
    bare = {k: v for k, v in SERVICE.items() if k != "description"}
    client.post("/api/service-entries", json=bare)
    assert client.post("/api/service-entries", json={**bare, "description": ""}).status_code == 409


def test_service_entry_with_different_description_or_type_is_not_duplicate(client):
    client.post("/api/service-entries", json=SERVICE)
    assert (
        client.post("/api/service-entries", json={**SERVICE, "description": "Brake pads"})
    ).status_code == 201
    assert (
        client.post("/api/service-entries", json={**SERVICE, "type": "tires"})
    ).status_code == 201


def test_duplicate_service_entry_saved_with_force(client):
    client.post("/api/service-entries", json=SERVICE)
    response = client.post("/api/service-entries?force=true", json=SERVICE)
    assert response.status_code == 201
    assert len(client.get("/api/service-entries").json()) == 2


def test_update_service_entry_ignores_itself(client):
    entry = client.post("/api/service-entries", json=SERVICE).json()
    response = client.put(f"/api/service-entries/{entry['id']}", json={**SERVICE, "cost": 90})
    assert response.status_code == 200

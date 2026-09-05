def test_create_fuel_entry_updates_car_mileage(client):
    response = client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["price_total"] == 60.0
    assert body["price_per_liter_czk"] == 1.5
    assert body["price_total_czk"] == 60.0
    assert body["consumption_l_per_100km"] is None

    car = client.get("/api/car").json()
    assert car["current_mileage_km"] == 10000


def test_consumption_computed_from_previous_entry(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    second = client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-05", "mileage_km": 10500, "liters": 35, "price_per_liter": 1.6},
    ).json()
    assert second["consumption_l_per_100km"] == 7.0


def test_list_fuel_entries_newest_first(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-05", "mileage_km": 10500, "liters": 35, "price_per_liter": 1.6},
    )
    entries = client.get("/api/fuel-entries").json()
    assert [e["mileage_km"] for e in entries] == [10500, 10000]


def test_delete_fuel_entry(client):
    created = client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    ).json()
    response = client.delete(f"/api/fuel-entries/{created['id']}")
    assert response.status_code == 204
    assert client.get("/api/fuel-entries").json() == []


def test_delete_missing_fuel_entry_404s(client):
    response = client.delete("/api/fuel-entries/999")
    assert response.status_code == 404


def test_delete_highest_mileage_entry_recalculates_car_mileage(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    second = client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-05", "mileage_km": 10500, "liters": 35, "price_per_liter": 1.6},
    ).json()

    client.delete(f"/api/fuel-entries/{second['id']}")
    car = client.get("/api/car").json()
    assert car["current_mileage_km"] == 10000


def test_update_fuel_entry(client):
    created = client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    ).json()

    updated = client.put(
        f"/api/fuel-entries/{created['id']}",
        json={"date": "2026-08-01", "mileage_km": 10050, "liters": 42, "price_per_liter": 1.55},
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["mileage_km"] == 10050
    assert body["liters"] == 42
    assert body["price_per_liter"] == 1.55

    car = client.get("/api/car").json()
    assert car["current_mileage_km"] == 10050


def test_update_missing_fuel_entry_404s(client):
    response = client.put(
        "/api/fuel-entries/999",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    assert response.status_code == 404


def test_create_fuel_entry_with_lower_mileage_than_history_is_rejected(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-05", "mileage_km": 10500, "liters": 35, "price_per_liter": 1.5},
    )
    response = client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-10", "mileage_km": 10200, "liters": 30, "price_per_liter": 1.5},
    )
    assert response.status_code == 400


def test_create_fuel_entry_backfilling_earlier_date_is_allowed(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-05", "mileage_km": 10500, "liters": 35, "price_per_liter": 1.5},
    )
    response = client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    assert response.status_code == 201


def test_partial_fill_has_no_consumption(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    partial = client.post(
        "/api/fuel-entries",
        json={
            "date": "2026-08-03",
            "mileage_km": 10300,
            "liters": 20,
            "price_per_liter": 1.5,
            "full_tank": False,
        },
    ).json()
    assert partial["full_tank"] is False
    assert partial["consumption_l_per_100km"] is None


def test_full_to_full_consumption_sums_liters_across_partial_fills(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    client.post(
        "/api/fuel-entries",
        json={
            "date": "2026-08-03",
            "mileage_km": 10300,
            "liters": 20,
            "price_per_liter": 1.5,
            "full_tank": False,
        },
    )
    next_full = client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-05", "mileage_km": 10500, "liters": 15, "price_per_liter": 1.5},
    ).json()
    # (20 partial + 15 full) liters over the 500 km since the last full tank.
    assert next_full["consumption_l_per_100km"] == 7.0


def test_create_fuel_entry_with_eur_converts_to_czk(client):
    client.put("/api/currency-rates/EUR", json={"rate_to_czk": 25.0})
    response = client.post(
        "/api/fuel-entries",
        json={
            "date": "2026-08-01",
            "mileage_km": 10000,
            "liters": 40,
            "price_per_liter": 1.5,
            "currency": "EUR",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["price_total"] == 60.0
    assert body["price_total_czk"] == 1500.0
    assert body["price_per_liter_czk"] == 37.5


def test_create_fuel_entry_with_exchange_rate_override_updates_settings_default(client):
    client.put("/api/currency-rates/EUR", json={"rate_to_czk": 25.0})
    response = client.post(
        "/api/fuel-entries",
        json={
            "date": "2026-08-01",
            "mileage_km": 10000,
            "liters": 40,
            "price_per_liter": 1.5,
            "currency": "EUR",
            "exchange_rate": 26.0,
        },
    )
    body = response.json()
    assert body["exchange_rate"] == 26.0
    assert body["price_per_liter_czk"] == 39.0

    rates = {r["currency"]: r["rate_to_czk"] for r in client.get("/api/currency-rates").json()}
    assert rates["EUR"] == 26.0


def test_create_fuel_entry_without_exchange_rate_override_uses_settings_default(client):
    client.put("/api/currency-rates/EUR", json={"rate_to_czk": 25.0})
    response = client.post(
        "/api/fuel-entries",
        json={
            "date": "2026-08-01",
            "mileage_km": 10000,
            "liters": 40,
            "price_per_liter": 1.5,
            "currency": "EUR",
        },
    )
    body = response.json()
    assert body["exchange_rate"] == 25.0

    rates = {r["currency"]: r["rate_to_czk"] for r in client.get("/api/currency-rates").json()}
    assert rates["EUR"] == 25.0

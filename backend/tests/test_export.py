def test_export_fuel_csv(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    response = client.get("/api/export/fuel.csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    body = response.text
    assert "2026-08-01" in body
    assert "40" in body


def test_export_maintenance_csv(client):
    client.post(
        "/api/service-entries",
        json={"date": "2026-08-02", "mileage_km": 10200, "type": "oil_change", "cost": 80},
    )
    response = client.get("/api/export/maintenance.csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "oil_change" in response.text


def test_export_fuel_csv_orders_same_day_fill_ups_by_mileage(client):
    for mileage_km in (10300, 10000):
        client.post(
            "/api/fuel-entries",
            json={
                "date": "2026-08-22",
                "mileage_km": mileage_km,
                "liters": 20,
                "price_per_liter": 1.5,
            },
        )
    body = client.get("/api/export/fuel.csv").text
    assert body.index("10000") < body.index("10300")

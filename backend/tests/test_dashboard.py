def _fuel(client, date, mileage_km, liters, *, full_tank=True):
    response = client.post(
        "/api/fuel-entries",
        json={
            "date": date,
            "mileage_km": mileage_km,
            "liters": liters,
            "price_per_liter": 1.0,
            "full_tank": full_tank,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_fuel_trend_is_chronological(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-05", "mileage_km": 10500, "liters": 35, "price_per_liter": 1.6},
    )
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    trend = client.get("/api/dashboard").json()["fuel_trend"]
    assert [p["date"] for p in trend] == ["2026-08-01", "2026-08-05"]


def test_fuel_trend_converts_to_czk(client):
    client.post(
        "/api/fuel-entries",
        json={
            "date": "2026-08-01",
            "mileage_km": 10000,
            "liters": 40,
            "price_per_liter": 1.5,
            "currency": "EUR",
        },
    )
    trend = client.get("/api/dashboard").json()["fuel_trend"]
    assert trend[0]["price_total"] == 1500.0


def test_cost_breakdown_groups_by_service_type(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    client.post(
        "/api/service-entries",
        json={"date": "2026-08-02", "mileage_km": 10200, "type": "oil_change", "cost": 80},
    )
    client.post(
        "/api/service-entries",
        json={"date": "2026-08-03", "mileage_km": 10300, "type": "oil_change", "cost": 20},
    )
    breakdown = client.get("/api/dashboard").json()["cost_breakdown"]
    assert breakdown["fuel_total"] == 60
    assert breakdown["maintenance_by_type"] == {"oil_change": 100}


def test_avg_consumption_is_distance_weighted(client):
    # 1000 km on 50 l (5 l/100 km), then 100 km on 20 l (20 l/100 km). The mean
    # of the two readings is 12.5; weighted by distance it is 70 l / 1100 km.
    _fuel(client, "2026-01-01", 10000, 40)
    _fuel(client, "2026-02-01", 11000, 50)
    _fuel(client, "2026-03-01", 11100, 20)

    dashboard = client.get("/api/dashboard").json()
    assert dashboard["avg_consumption_l_per_100km"] == round(70 / 1100 * 100, 2)


def test_avg_consumption_counts_partial_fills_toward_the_next_full_tank(client):
    # The partial fill closes no interval of its own; its liters land in the
    # 10000 -> 11000 stretch, giving 50 l / 1000 km.
    _fuel(client, "2026-01-01", 10000, 40)
    _fuel(client, "2026-01-15", 10500, 20, full_tank=False)
    _fuel(client, "2026-02-01", 11000, 30)

    dashboard = client.get("/api/dashboard").json()
    assert dashboard["avg_consumption_l_per_100km"] == 5.0


def test_avg_consumption_splits_by_year(client):
    # 2025: 400 km on 20 l = 5 l/100 km. 2026: 200 km on 20 l = 10 l/100 km.
    # All time: 40 l / 600 km = 6.67.
    _fuel(client, "2025-01-01", 10000, 30)
    _fuel(client, "2025-06-01", 10400, 20)
    _fuel(client, "2026-06-01", 10600, 20)

    def avg(period):
        return client.get("/api/dashboard", params={"period": period}).json()[
            "avg_consumption_l_per_100km"
        ]

    assert avg("year:2025") == 5.0
    assert avg("year:2026") == 10.0
    assert avg("all") == round(40 / 600 * 100, 2)


def test_avg_consumption_is_none_with_no_closed_interval(client):
    # A single fill-up opens an interval but closes none, so there is nothing
    # to measure.
    _fuel(client, "2026-01-01", 10000, 40)

    dashboard = client.get("/api/dashboard").json()
    assert dashboard["avg_consumption_l_per_100km"] is None
    assert dashboard["consumption_interval_count"] == 0

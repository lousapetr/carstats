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


def test_summary_on_empty_data(client):
    summary = client.get("/api/dashboard/summary").json()
    assert summary["total_fuel_cost"] == 0
    assert summary["total_maintenance_cost"] == 0
    assert summary["avg_consumption_l_per_100km"] is None
    assert summary["avg_consumption_l_per_100km_this_year"] is None
    assert summary["avg_consumption_l_per_100km_last_year"] is None
    assert summary["cost_per_km"] is None
    assert summary["upcoming_reminders"] == []
    assert summary["recent_activity"] == []


def test_summary_aggregates_costs_and_activity(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-05", "mileage_km": 10500, "liters": 35, "price_per_liter": 1.6},
    )
    client.post(
        "/api/service-entries",
        json={"date": "2026-08-02", "mileage_km": 10200, "type": "oil_change", "cost": 80},
    )

    summary = client.get("/api/dashboard/summary").json()
    assert summary["total_fuel_cost"] == 116
    assert summary["total_fuel_entries"] == 2
    assert summary["total_maintenance_cost"] == 80
    assert summary["total_cost"] == 196
    assert summary["avg_consumption_l_per_100km"] == 7.0
    assert len(summary["recent_activity"]) == 3
    assert summary["recent_activity"][0]["date"] == "2026-08-05"
    # 500 km driven (10000 -> 10500) for 196 total cost.
    assert summary["cost_per_km"] == round(196 / 500, 2)


def test_summary_splits_this_year_and_last_year(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2020-01-01", "mileage_km": 9000, "liters": 40, "price_per_liter": 1.5},
    )
    client.post(
        "/api/fuel-entries",
        json={"date": "2025-01-01", "mileage_km": 9500, "liters": 40, "price_per_liter": 2.0},
    )
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-01-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    summary = client.get("/api/dashboard/summary").json()
    assert summary["total_cost_this_year"] == 60
    assert summary["total_cost_last_year"] == 80


def test_fuel_trend_is_chronological(client):
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-05", "mileage_km": 10500, "liters": 35, "price_per_liter": 1.6},
    )
    client.post(
        "/api/fuel-entries",
        json={"date": "2026-08-01", "mileage_km": 10000, "liters": 40, "price_per_liter": 1.5},
    )
    trend = client.get("/api/dashboard/fuel-trend").json()
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
    trend = client.get("/api/dashboard/fuel-trend").json()
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
    breakdown = client.get("/api/dashboard/cost-breakdown").json()
    assert breakdown["fuel_total"] == 60
    assert breakdown["maintenance_by_type"] == {"oil_change": 100}


def test_avg_consumption_is_distance_weighted(client):
    # 1000 km on 50 l (5 l/100 km), then 100 km on 20 l (20 l/100 km). The mean
    # of the two readings is 12.5; weighted by distance it is 70 l / 1100 km.
    _fuel(client, "2026-01-01", 10000, 40)
    _fuel(client, "2026-02-01", 11000, 50)
    _fuel(client, "2026-03-01", 11100, 20)

    summary = client.get("/api/dashboard/summary").json()
    assert summary["avg_consumption_l_per_100km"] == round(70 / 1100 * 100, 2)


def test_avg_consumption_counts_partial_fills_toward_the_next_full_tank(client):
    # The partial fill closes no interval of its own; its liters land in the
    # 10000 -> 11000 stretch, giving 50 l / 1000 km.
    _fuel(client, "2026-01-01", 10000, 40)
    _fuel(client, "2026-01-15", 10500, 20, full_tank=False)
    _fuel(client, "2026-02-01", 11000, 30)

    summary = client.get("/api/dashboard/summary").json()
    assert summary["avg_consumption_l_per_100km"] == 5.0


def test_avg_consumption_splits_this_year_and_last_year(client):
    # 2025: 400 km on 20 l = 5 l/100 km. 2026: 200 km on 20 l = 10 l/100 km.
    # All time: 40 l / 600 km = 6.67.
    _fuel(client, "2025-01-01", 10000, 30)
    _fuel(client, "2025-06-01", 10400, 20)
    _fuel(client, "2026-06-01", 10600, 20)

    summary = client.get("/api/dashboard/summary").json()
    assert summary["avg_consumption_l_per_100km_last_year"] == 5.0
    assert summary["avg_consumption_l_per_100km_this_year"] == 10.0
    assert summary["avg_consumption_l_per_100km"] == round(40 / 600 * 100, 2)


def test_avg_consumption_is_none_for_a_year_with_no_closed_interval(client):
    # A single fill-up opens an interval but closes none, so there is nothing
    # to measure in either year.
    _fuel(client, "2026-01-01", 10000, 40)

    summary = client.get("/api/dashboard/summary").json()
    assert summary["avg_consumption_l_per_100km"] is None
    assert summary["avg_consumption_l_per_100km_this_year"] is None
    assert summary["avg_consumption_l_per_100km_last_year"] is None

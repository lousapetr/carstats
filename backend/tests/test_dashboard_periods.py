from datetime import date

import pytest

from app.dashboard import service
from app.dashboard.periods import DateWindow, parse_period, previous_window

TODAY = date(2026, 9, 30)


class _FixedDate(date):
    @classmethod
    def today(cls) -> "_FixedDate":
        return cls(TODAY.year, TODAY.month, TODAY.day)


@pytest.fixture()
def fixed_today(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(service, "date", _FixedDate)


def _fuel(client, date, mileage_km, liters, *, price_per_liter=1.0, full_tank=True):
    response = client.post(
        "/api/fuel-entries",
        json={
            "date": date,
            "mileage_km": mileage_km,
            "liters": liters,
            "price_per_liter": price_per_liter,
            "full_tank": full_tank,
        },
    )
    assert response.status_code == 201, response.text


def _service(client, date, mileage_km, cost):
    response = client.post(
        "/api/service-entries",
        json={"date": date, "mileage_km": mileage_km, "type": "oil_change", "cost": cost},
    )
    assert response.status_code == 201, response.text


def _dashboard(client, period="all"):
    response = client.get("/api/dashboard", params={"period": period})
    assert response.status_code == 200, response.text
    return response.json()


# --- window arithmetic ---


def test_all_is_unbounded_with_no_previous_window():
    assert parse_period("all", TODAY) == DateWindow(None, None)
    assert previous_window("all", TODAY) is None


def test_ytd_window_and_date_aligned_previous():
    assert parse_period("ytd", TODAY) == DateWindow(date(2026, 1, 1), TODAY)
    assert previous_window("ytd", TODAY) == DateWindow(date(2025, 1, 1), date(2025, 9, 30))


def test_ytd_previous_on_a_leap_day_ends_on_28_february():
    leap_day = date(2028, 2, 29)
    assert previous_window("ytd", leap_day) == DateWindow(date(2027, 1, 1), date(2027, 2, 28))


def test_12m_is_twelve_whole_month_buckets():
    assert parse_period("12m", TODAY) == DateWindow(date(2025, 10, 1), TODAY)
    assert previous_window("12m", TODAY) == DateWindow(date(2024, 10, 1), date(2025, 9, 30))


def test_12m_crosses_the_year_boundary_from_january():
    assert parse_period("12m", date(2026, 1, 15)) == DateWindow(date(2025, 2, 1), date(2026, 1, 15))


def test_year_window_and_previous():
    assert parse_period("year:2024", TODAY) == DateWindow(date(2024, 1, 1), date(2024, 12, 31))
    assert previous_window("year:2024", TODAY) == DateWindow(date(2023, 1, 1), date(2023, 12, 31))


def test_window_bounds_are_inclusive():
    window = parse_period("year:2024", TODAY)
    assert window.contains(date(2024, 1, 1))
    assert window.contains(date(2024, 12, 31))
    assert not window.contains(date(2023, 12, 31))
    assert not window.contains(date(2025, 1, 1))


# --- endpoint ---


@pytest.mark.parametrize("period", ["", "last", "year:26", "year:0999", "YTD", "all "])
def test_invalid_period_is_422(client, period):
    assert client.get("/api/dashboard", params={"period": period}).status_code == 422


def test_dashboard_requires_login(anon_client):
    assert anon_client.get("/api/dashboard").status_code == 401


def test_all_reproduces_the_summary_figures(client):
    _fuel(client, "2026-08-01", 10000, 40, price_per_liter=1.5)
    _fuel(client, "2026-08-05", 10500, 35, price_per_liter=1.6)
    _service(client, "2026-08-02", 10200, 80)

    dashboard = _dashboard(client)
    assert dashboard["totals"] == {
        "fuel": 116,
        "fuel_liters": 75,
        "fuel_entries": 2,
        "maintenance": 80,
        "maintenance_entries": 1,
        "total": 196,
    }
    assert dashboard["previous_totals"] is None
    assert dashboard["total_cost_delta_pct"] is None
    assert dashboard["distance_km"] == 500
    assert dashboard["cost_per_km"] == round(196 / 500, 2)
    assert dashboard["avg_consumption_l_per_100km"] == 7.0
    assert dashboard["consumption_interval_count"] == 1
    assert dashboard["cost_breakdown"] == {
        "fuel_total": 116,
        "maintenance_by_type": {"oil_change": 80},
    }
    assert [p["date"] for p in dashboard["fuel_trend"]] == ["2026-08-01", "2026-08-05"]
    assert len(dashboard["recent_activity"]) == 3
    assert dashboard["available_years"] == [2026]


def test_empty_dashboard(client):
    dashboard = _dashboard(client)
    assert dashboard["totals"]["total"] == 0
    assert dashboard["distance_km"] is None
    assert dashboard["cost_per_km"] is None
    assert dashboard["avg_consumption_l_per_100km"] is None
    assert dashboard["consumption_interval_count"] == 0
    assert dashboard["monthly_costs"] == []
    assert dashboard["available_years"] == []


def test_costs_filter_by_entry_date(client, fixed_today):
    _fuel(client, "2025-06-01", 10000, 40)
    _fuel(client, "2026-06-01", 11000, 30)
    _service(client, "2025-07-01", 10500, 100)

    ytd = _dashboard(client, "ytd")
    assert ytd["totals"]["total"] == 30
    assert ytd["previous_totals"]["total"] == 140
    assert ytd["total_cost_delta_pct"] == round((30 - 140) / 140 * 100, 1)
    assert [a["date"] for a in ytd["recent_activity"]] == ["2026-06-01"]

    year_2025 = _dashboard(client, "year:2025")
    assert year_2025["totals"]["total"] == 140
    assert year_2025["previous_totals"]["total"] == 0
    assert year_2025["total_cost_delta_pct"] is None
    assert year_2025["cost_breakdown"]["maintenance_by_type"] == {"oil_change": 100}


def test_ytd_previous_excludes_the_rest_of_last_year(client, fixed_today):
    _fuel(client, "2025-09-30", 10000, 40)
    _fuel(client, "2025-10-01", 10500, 40)

    ytd = _dashboard(client, "ytd")
    assert ytd["previous_totals"]["total"] == 40


def test_interval_straddling_the_window_start_counts_under_its_closing_year(client, fixed_today):
    # The tank opened in December and closed in January covers 500 km on
    # 20 + 30 litres, the December partial fill included. Filtering entries
    # first would drop the interval entirely.
    _fuel(client, "2025-12-01", 10000, 40)
    _fuel(client, "2025-12-20", 10200, 20, full_tank=False)
    _fuel(client, "2026-01-05", 10500, 30)

    ytd = _dashboard(client, "ytd")
    assert ytd["avg_consumption_l_per_100km"] == 10.0
    assert ytd["consumption_interval_count"] == 1

    year_2025 = _dashboard(client, "year:2025")
    assert year_2025["avg_consumption_l_per_100km"] is None
    assert year_2025["consumption_interval_count"] == 0


def test_avg_consumption_delta_is_absolute(client, fixed_today):
    # 2025: 400 km on 20 l = 5 l/100 km. 2026: 200 km on 20 l = 10 l/100 km.
    _fuel(client, "2025-01-01", 10000, 30)
    _fuel(client, "2025-06-01", 10400, 20)
    _fuel(client, "2026-06-01", 10600, 20)

    dashboard = _dashboard(client, "year:2026")
    assert dashboard["avg_consumption_l_per_100km"] == 10.0
    assert dashboard["avg_consumption_delta"] == 5.0


def test_cost_per_km_anchors_to_the_last_reading_before_the_window(client, fixed_today):
    # Km driven between the December fill-up and the first 2026 entry belong
    # to 2026 too: 10000 -> 11000 is 1000 km, not the 500 km between 2026's
    # own readings.
    _fuel(client, "2025-12-20", 10000, 40)
    _fuel(client, "2026-03-01", 10500, 50)
    _fuel(client, "2026-06-01", 11000, 50)

    ytd = _dashboard(client, "ytd")
    assert ytd["distance_km"] == 1000
    assert ytd["cost_per_km"] == round(100 / 1000, 2)


def test_past_window_ends_at_its_newest_reading_not_the_odometer(client, fixed_today):
    _fuel(client, "2024-01-01", 10000, 40)
    _fuel(client, "2024-12-01", 12000, 40)
    _fuel(client, "2026-01-01", 20000, 40)

    year_2024 = _dashboard(client, "year:2024")
    assert year_2024["distance_km"] == 2000


def test_monthly_costs_seed_every_month_with_zero(client, fixed_today):
    _fuel(client, "2026-02-10", 10000, 40)
    _service(client, "2026-02-15", 10100, 100)
    _fuel(client, "2026-04-10", 10500, 30)

    ytd = _dashboard(client, "ytd")
    assert ytd["monthly_granularity"] == "month"
    assert [p["bucket"] for p in ytd["monthly_costs"]] == [f"2026-{m:02d}" for m in range(1, 10)]
    by_bucket = {p["bucket"]: p for p in ytd["monthly_costs"]}
    assert by_bucket["2026-02"] == {"bucket": "2026-02", "fuel": 40, "service": 100}
    assert by_bucket["2026-03"] == {"bucket": "2026-03", "fuel": 0, "service": 0}


def test_monthly_costs_switch_to_years_past_36_months(client, fixed_today):
    # Oct 2023 .. Sep 2026 is exactly 36 months; one month earlier tips it over.
    _fuel(client, "2023-10-01", 10000, 40)
    assert _dashboard(client)["monthly_granularity"] == "month"
    assert len(_dashboard(client)["monthly_costs"]) == 36

    _fuel(client, "2023-09-01", 9000, 40)
    dashboard = _dashboard(client)
    assert dashboard["monthly_granularity"] == "year"
    assert [p["bucket"] for p in dashboard["monthly_costs"]] == ["2023", "2024", "2025", "2026"]
    assert dashboard["monthly_costs"][0]["fuel"] == 80


def test_available_years_are_newest_first(client):
    _fuel(client, "2024-01-01", 10000, 40)
    _service(client, "2025-01-01", 11000, 10)
    _fuel(client, "2026-01-01", 12000, 40)
    assert _dashboard(client)["available_years"] == [2026, 2025, 2024]

import logging
from datetime import timedelta

from app.currency.cnb_client import parse_rates
from app.currency.models import Currency

CNB_SAMPLE = """05.09.2026 #172
Country|Currency|Amount|Code|Rate
EMU|euro|1|EUR|25.185
Hungary|forint|100|HUF|6.234
Japan|yen|100|JPY|15.678
USA|dollar|1|USD|22.678
"""


def test_parse_rates_normalizes_by_amount():
    rates = parse_rates(CNB_SAMPLE)
    assert rates[Currency.EUR] == 25.185
    assert rates[Currency.HUF] == 0.06234


def test_parse_rates_ignores_unsupported_currencies():
    rates = parse_rates(CNB_SAMPLE)
    assert "JPY" not in {c.value for c in rates}
    assert "USD" not in {c.value for c in rates}


def test_list_currency_rates_fetches_from_cnb(client):
    rates = client.get("/api/currency-rates").json()
    currencies = {r["currency"] for r in rates}
    assert currencies == {"EUR", "PLN", "HUF", "GBP", "CHF", "SEK", "NOK", "DKK", "RON"}
    eur = next(r for r in rates if r["currency"] == "EUR")
    assert eur["rate_to_czk"] == 25.0  # from conftest's stubbed CNB_SAMPLE_TEXT


def test_currency_rates_fetched_at_most_once_per_day(client, monkeypatch):
    calls = 0

    def fake_fetch() -> str:
        nonlocal calls
        calls += 1
        return CNB_SAMPLE

    monkeypatch.setattr("app.currency.cnb_client.fetch_daily_text", fake_fetch)

    client.get("/api/currency-rates")
    client.get("/api/currency-rates")
    assert calls == 1


def test_currency_rates_fall_back_to_seeded_defaults_when_cnb_unreachable(
    client, monkeypatch, caplog
):
    def fake_fetch() -> str:
        raise ConnectionError("network down")

    monkeypatch.setattr("app.currency.cnb_client.fetch_daily_text", fake_fetch)

    with caplog.at_level(logging.WARNING, logger="app.currency.service"):
        response = client.get("/api/currency-rates")
    assert response.status_code == 200
    eur = next(r for r in response.json() if r["currency"] == "EUR")
    assert eur["rate_to_czk"] == 25.20  # DEFAULT_RATES_TO_CZK fallback
    assert "network down" in caplog.text


def test_unparseable_cnb_response_falls_back_and_logs(client, monkeypatch, caplog):
    monkeypatch.setattr(
        "app.currency.cnb_client.fetch_daily_text",
        lambda: "05.09.2026 #172\nCountry|Currency|Amount|Code|Rate\nunexpected format\n",
    )

    with caplog.at_level(logging.WARNING, logger="app.currency.service"):
        response = client.get("/api/currency-rates")
    assert response.status_code == 200
    eur = next(r for r in response.json() if r["currency"] == "EUR")
    assert eur["rate_to_czk"] == 25.20
    assert "keeping cached rates" in caplog.text


def test_parse_rates_skips_rows_with_zero_amount():
    text = CNB_SAMPLE.replace("Hungary|forint|100|HUF|6.234", "Hungary|forint|0|HUF|6.234")

    rates = parse_rates(text)

    assert Currency.HUF not in rates
    assert rates[Currency.EUR] == 25.185


def test_parse_rates_skips_malformed_rows():
    text = CNB_SAMPLE.replace("Hungary|forint|100|HUF|6.234", "Hungary|forint|HUF")

    rates = parse_rates(text)

    assert Currency.HUF not in rates
    assert rates[Currency.EUR] == 25.185


def test_parse_rates_returns_empty_for_an_entirely_malformed_feed():
    assert parse_rates("05.09.2026 #172\nCountry|Currency|Amount|Code|Rate\nnonsense\n") == {}


def test_zero_amount_in_the_feed_does_not_break_entry_creation(client, monkeypatch):
    """A zero Amount column used to raise ZeroDivisionError past the caller's
    except tuple and 500 the request (issue #7)."""
    monkeypatch.setattr(
        "app.currency.cnb_client.fetch_daily_text",
        lambda: CNB_SAMPLE.replace("EMU|euro|1|EUR|25.185", "EMU|euro|0|EUR|25.185"),
    )

    response = client.post(
        "/api/fuel-entries",
        json={
            "date": "2026-09-05",
            "mileage_km": 10500,
            "liters": 40,
            "price_per_liter": 1.5,
            "currency": "EUR",
        },
    )

    assert response.status_code == 201
    assert response.json()["exchange_rate"] == 25.20  # DEFAULT_RATES_TO_CZK fallback


def test_failed_fetch_does_not_pin_seeded_defaults_for_the_rest_of_the_day(client, monkeypatch):
    """Seeding used to stamp updated_at=now, which made the cache look fresh and
    suppressed every retry that day (issue #6)."""
    monkeypatch.setattr("app.currency.service.FETCH_RETRY_AFTER", timedelta(0))
    monkeypatch.setattr(
        "app.currency.cnb_client.fetch_daily_text",
        lambda: (_ for _ in ()).throw(ConnectionError("network down")),
    )

    first = client.get("/api/currency-rates").json()
    assert next(r for r in first if r["currency"] == "EUR")["rate_to_czk"] == 25.20

    monkeypatch.setattr("app.currency.cnb_client.fetch_daily_text", lambda: CNB_SAMPLE)

    second = client.get("/api/currency-rates").json()
    assert next(r for r in second if r["currency"] == "EUR")["rate_to_czk"] == 25.185


def test_failed_fetch_backs_off_before_retrying(client, monkeypatch):
    calls = 0

    def failing_fetch() -> str:
        nonlocal calls
        calls += 1
        raise ConnectionError("network down")

    monkeypatch.setattr("app.currency.cnb_client.fetch_daily_text", failing_fetch)

    client.get("/api/currency-rates")
    client.get("/api/currency-rates")

    assert calls == 1

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


def test_currency_rates_fall_back_to_seeded_defaults_when_cnb_unreachable(client, monkeypatch):
    def fake_fetch() -> str:
        raise ConnectionError("network down")

    monkeypatch.setattr("app.currency.cnb_client.fetch_daily_text", fake_fetch)

    response = client.get("/api/currency-rates")
    assert response.status_code == 200
    eur = next(r for r in response.json() if r["currency"] == "EUR")
    assert eur["rate_to_czk"] == 25.20  # DEFAULT_RATES_TO_CZK fallback

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


def test_list_currency_rates_seeds_defaults(client):
    rates = client.get("/api/currency-rates").json()
    currencies = {r["currency"] for r in rates}
    assert currencies == {"EUR", "PLN", "HUF", "GBP", "CHF", "SEK", "NOK", "DKK", "RON"}
    eur = next(r for r in rates if r["currency"] == "EUR")
    assert eur["rate_to_czk"] == 25.20


def test_update_currency_rate(client):
    response = client.put("/api/currency-rates/EUR", json={"rate_to_czk": 26.5})
    assert response.status_code == 200
    assert response.json()["rate_to_czk"] == 26.5

    rates = client.get("/api/currency-rates").json()
    eur = next(r for r in rates if r["currency"] == "EUR")
    assert eur["rate_to_czk"] == 26.5


def test_cannot_update_czk_rate(client):
    response = client.put("/api/currency-rates/CZK", json={"rate_to_czk": 2.0})
    assert response.status_code == 400

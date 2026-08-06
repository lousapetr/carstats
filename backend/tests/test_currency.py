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

import httpx

from app.currency.models import Currency

CNB_DAILY_RATES_URL = (
    "https://www.cnb.cz/en/financial-markets/foreign-exchange-market/"
    "central-bank-exchange-rate-fixing/central-bank-exchange-rate-fixing/daily.txt"
)


def fetch_daily_text() -> str:
    response = httpx.get(CNB_DAILY_RATES_URL, timeout=10.0)
    response.raise_for_status()
    return response.text


def parse_rates(text: str) -> dict[Currency, float]:
    """Parse ČNB's daily fixing text into {currency: rate_to_czk per 1 unit}.

    Format is two header lines (date + column names) followed by one row
    per currency: Country|Currency|Amount|Code|Rate. Amount matters — some
    currencies (e.g. HUF) are quoted per 100 units, not per 1.
    """
    rates: dict[Currency, float] = {}
    lines = text.strip().splitlines()[2:]
    for line in lines:
        _country, _name, amount, code, rate = line.split("|")
        try:
            currency = Currency(code)
        except ValueError:
            continue
        rates[currency] = float(rate) / float(amount)
    return rates

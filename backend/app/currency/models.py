from datetime import UTC, datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


class Currency(StrEnum):
    CZK = "CZK"
    EUR = "EUR"
    PLN = "PLN"
    HUF = "HUF"
    GBP = "GBP"
    CHF = "CHF"
    SEK = "SEK"
    NOK = "NOK"
    DKK = "DKK"
    RON = "RON"


# Starting presets (approximate 2025 averages) — editable in Settings.
# CZK itself is not stored: its rate is always 1.0.
DEFAULT_RATES_TO_CZK: dict[Currency, float] = {
    Currency.EUR: 25.20,
    Currency.GBP: 29.80,
    Currency.CHF: 27.00,
    Currency.PLN: 5.85,
    Currency.RON: 5.05,
    Currency.SEK: 2.20,
    Currency.NOK: 2.10,
    Currency.DKK: 3.38,
    Currency.HUF: 0.0635,
}


class CurrencyRate(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    currency: Currency = Field(unique=True)
    rate_to_czk: float
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

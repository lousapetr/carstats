from datetime import UTC, date, datetime

from sqlmodel import Field, SQLModel

from app.currency.models import Currency


class FuelEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    date: date
    mileage_km: float
    liters: float
    price_per_liter: float  # in the original currency
    currency: Currency = Currency.CZK
    exchange_rate: float = 1.0  # rate_to_czk snapshot at entry time
    full_tank: bool = Field(default=True)
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

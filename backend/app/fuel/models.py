from datetime import UTC, date, datetime

from sqlmodel import Field, SQLModel

from app.currency.models import Currency


class FuelEntryBase(SQLModel):
    date: date
    mileage_km: float
    liters: float
    price_per_liter: float
    currency: Currency = Currency.CZK
    full_tank: bool = True
    notes: str | None = None


class FuelEntry(FuelEntryBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    exchange_rate: float = 1.0  # rate_to_czk snapshot at entry time
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FuelEntryCreate(FuelEntryBase):
    pass


class FuelEntryRead(FuelEntryBase):
    id: int
    exchange_rate: float  # rate_to_czk snapshot used for this entry
    price_per_liter_czk: float
    price_total: float  # original-currency total (liters * price_per_liter)
    price_total_czk: float
    # Full-to-full accounting: only set on full-tank entries, as liters
    # since the previous full tank divided by the mileage delta between them.
    consumption_l_per_100km: float | None = None

from datetime import date

from pydantic import BaseModel

from app.currency.models import Currency


class FuelEntryCreate(BaseModel):
    date: date
    mileage_km: float
    liters: float
    price_per_liter: float
    currency: Currency = Currency.CZK
    notes: str | None = None


class FuelEntryRead(FuelEntryCreate):
    id: int
    price_per_liter_czk: float
    price_total: float  # original-currency total (liters * price_per_liter)
    price_total_czk: float
    # Consumption since the previous entry by mileage, if one exists.
    consumption_l_per_100km: float | None = None

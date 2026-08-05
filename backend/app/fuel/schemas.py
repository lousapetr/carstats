from datetime import date

from pydantic import BaseModel


class FuelEntryCreate(BaseModel):
    date: date
    mileage_km: float
    liters: float
    price_total: float
    notes: str | None = None


class FuelEntryRead(FuelEntryCreate):
    id: int
    price_per_liter: float
    # Consumption since the previous entry, if one exists (None for the first entry).
    consumption_l_per_100km: float | None = None

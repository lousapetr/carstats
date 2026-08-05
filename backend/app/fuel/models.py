from datetime import UTC, date, datetime

from sqlmodel import Field, SQLModel


class FuelEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    date: date
    mileage_km: float
    liters: float
    price_total: float
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

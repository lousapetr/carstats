from datetime import UTC, date, datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


class ServiceType(StrEnum):
    oil_change = "oil_change"
    tires = "tires"
    engine_service = "engine_service"
    other = "other"


class ServiceEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    date: date
    mileage_km: float
    type: ServiceType
    description: str | None = None
    cost: float
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

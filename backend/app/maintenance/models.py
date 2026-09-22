from datetime import UTC, date, datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel

from app.attachments.models import AttachmentRead
from app.currency.models import Currency


class ServiceType(StrEnum):
    oil_change = "oil_change"
    tires = "tires"
    engine_service = "engine_service"
    additives = "additives"
    other = "other"


class ServiceEntryBase(SQLModel):
    date: date
    mileage_km: float
    type: ServiceType
    description: str | None = None
    cost: float  # in the original currency
    currency: Currency = Currency.CZK
    notes: str | None = None


class ServiceEntry(ServiceEntryBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    exchange_rate: float = 1.0  # rate_to_czk snapshot at entry time
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ServiceEntryCreate(ServiceEntryBase):
    pass


class ServiceEntryRead(ServiceEntryBase):
    id: int
    exchange_rate: float  # rate_to_czk snapshot used for this entry
    cost_czk: float
    attachments: list[AttachmentRead] = []

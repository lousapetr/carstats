from datetime import UTC, datetime
from datetime import date as date_type
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
    # `date_type` because pydantic cannot resolve an annotation shadowed
    # by the field's own name once the field carries a Field(...).
    date: date_type = Field(index=True)
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
    # Bounds live here rather than on the base so an already-stored
    # out-of-range row still serialises through ServiceEntryRead.
    mileage_km: float = Field(ge=0)
    description: str | None = Field(default=None, max_length=1000)
    cost: float = Field(ge=0)
    notes: str | None = Field(default=None, max_length=1000)


class ServiceEntryRead(ServiceEntryBase):
    id: int
    exchange_rate: float  # rate_to_czk snapshot used for this entry
    cost_czk: float
    attachments: list[AttachmentRead] = []

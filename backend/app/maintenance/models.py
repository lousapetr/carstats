from datetime import UTC, datetime
from datetime import date as date_type
from enum import StrEnum
from typing import Self

from pydantic import model_validator
from sqlmodel import Field, SQLModel

from app.attachments.models import AttachmentRead
from app.core.drafts import draft_empty_error, has_content, missing_fields_error
from app.currency.models import Currency


class ServiceType(StrEnum):
    oil_change = "oil_change"
    tires = "tires"
    engine_service = "engine_service"
    additives = "additives"
    insurance = "insurance"
    vignette = "vignette"
    road_trip = "road_trip"
    inspection = "inspection"
    fines = "fines"
    other = "other"


class ServiceEntryBase(SQLModel):
    # `date_type` because pydantic cannot resolve an annotation shadowed
    # by the field's own name once the field carries a Field(...).
    # A draft may leave date, mileage and cost empty; a complete entry never does.
    date: date_type | None = Field(default=None, index=True)
    mileage_km: float | None = None
    type: ServiceType
    description: str | None = None
    cost: float | None = None  # in the original currency
    currency: Currency = Currency.CZK
    notes: str | None = None
    is_draft: bool = False


class ServiceEntry(ServiceEntryBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    exchange_rate: float = 1.0  # rate_to_czk snapshot at entry time
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ServiceEntryCreate(ServiceEntryBase):
    # Bounds live here rather than on the base so an already-stored
    # out-of-range row still serialises through ServiceEntryRead.
    mileage_km: float | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=1000)
    cost: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def _check_completeness(self) -> Self:
        if self.is_draft:
            if not has_content(self.mileage_km, self.cost, self.description, self.notes):
                raise draft_empty_error()
        else:
            missing = [
                label
                for label, value in (
                    ("datum", self.date),
                    ("stav tachometru", self.mileage_km),
                    ("cena", self.cost),
                )
                if value is None
            ]
            if missing:
                raise missing_fields_error(missing)
        return self


class ServiceEntryRead(ServiceEntryBase):
    id: int
    exchange_rate: float  # rate_to_czk snapshot used for this entry
    cost_czk: float | None  # None while cost is missing (drafts only)
    attachments: list[AttachmentRead] = []

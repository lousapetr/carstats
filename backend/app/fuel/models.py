from datetime import UTC, datetime
from datetime import date as date_type
from typing import Self

from pydantic import model_validator
from sqlmodel import Field, SQLModel

from app.core.drafts import draft_empty_error, has_content, missing_fields_error
from app.currency.models import Currency


class FuelEntryBase(SQLModel):
    # `date_type` because pydantic cannot resolve an annotation shadowed
    # by the field's own name once the field carries a Field(...).
    # A draft may leave date, mileage, liters and price empty; a complete entry never does.
    date: date_type | None = Field(default=None, index=True)
    mileage_km: float | None = None
    liters: float | None = None
    price_per_liter: float | None = None
    currency: Currency = Currency.CZK
    full_tank: bool = True
    notes: str | None = None
    is_draft: bool = False


class FuelEntry(FuelEntryBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    exchange_rate: float = 1.0  # rate_to_czk snapshot at entry time
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FuelEntryCreate(FuelEntryBase):
    # Bounds live here rather than on the base so an already-stored
    # out-of-range row still serialises through FuelEntryRead.
    mileage_km: float | None = Field(default=None, ge=0)
    liters: float | None = Field(default=None, gt=0)
    price_per_liter: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def _check_completeness(self) -> Self:
        if self.is_draft:
            if not has_content(self.mileage_km, self.liters, self.price_per_liter, self.notes):
                raise draft_empty_error()
        else:
            missing = [
                label
                for label, value in (
                    ("datum", self.date),
                    ("stav tachometru", self.mileage_km),
                    ("litry", self.liters),
                    ("cena za litr", self.price_per_liter),
                )
                if value is None
            ]
            if missing:
                raise missing_fields_error(missing)
        return self


class FuelEntryRead(FuelEntryBase):
    id: int
    exchange_rate: float  # rate_to_czk snapshot used for this entry
    # None while liters or price_per_liter is missing (drafts only).
    price_per_liter_czk: float | None
    price_total: float | None  # original-currency total (liters * price_per_liter)
    price_total_czk: float | None
    # Full-to-full accounting: only set on full-tank entries, as liters
    # since the previous full tank divided by the mileage delta between them.
    consumption_l_per_100km: float | None = None

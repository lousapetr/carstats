from datetime import date

from pydantic import BaseModel

from app.currency.models import Currency
from app.maintenance.models import ServiceType


class ServiceEntryCreate(BaseModel):
    date: date
    mileage_km: float
    type: ServiceType
    description: str | None = None
    cost: float
    currency: Currency = Currency.CZK
    notes: str | None = None


class AttachmentRead(BaseModel):
    id: int
    filename: str
    content_type: str


class ServiceEntryRead(ServiceEntryCreate):
    id: int
    cost_czk: float
    attachments: list[AttachmentRead] = []

from datetime import date

from pydantic import BaseModel

from app.maintenance.models import ServiceType


class ServiceEntryCreate(BaseModel):
    date: date
    mileage_km: float
    type: ServiceType
    description: str | None = None
    cost: float
    notes: str | None = None


class AttachmentRead(BaseModel):
    id: int
    filename: str
    content_type: str


class ServiceEntryRead(ServiceEntryCreate):
    id: int
    attachments: list[AttachmentRead] = []

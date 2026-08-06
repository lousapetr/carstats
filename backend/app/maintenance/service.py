from sqlmodel import Session, select

from app.attachments.models import Attachment
from app.car.service import (
    recalculate_current_mileage,
    validate_mileage_consistency,
)
from app.currency.service import get_rate
from app.maintenance.models import ServiceEntry
from app.maintenance.schemas import AttachmentRead, ServiceEntryCreate, ServiceEntryRead


def _to_read(entry: ServiceEntry, attachments: list[Attachment]) -> ServiceEntryRead:
    return ServiceEntryRead(
        id=entry.id,
        date=entry.date,
        mileage_km=entry.mileage_km,
        type=entry.type,
        description=entry.description,
        cost=entry.cost,
        currency=entry.currency,
        cost_czk=round(entry.cost * entry.exchange_rate, 2),
        notes=entry.notes,
        attachments=[
            AttachmentRead(id=a.id, filename=a.filename, content_type=a.content_type)
            for a in attachments
        ],
    )


def _attachments_for(db: Session, entry_id: int) -> list[Attachment]:
    return db.exec(select(Attachment).where(Attachment.service_entry_id == entry_id)).all()


def create_entry(db: Session, data: ServiceEntryCreate) -> ServiceEntryRead:
    validate_mileage_consistency(db, data.date, data.mileage_km)
    exchange_rate = get_rate(db, data.currency)

    entry = ServiceEntry(
        date=data.date,
        mileage_km=data.mileage_km,
        type=data.type,
        description=data.description,
        cost=data.cost,
        currency=data.currency,
        exchange_rate=exchange_rate,
        notes=data.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    recalculate_current_mileage(db)
    return _to_read(entry, [])


def update_entry(db: Session, entry: ServiceEntry, data: ServiceEntryCreate) -> ServiceEntryRead:
    validate_mileage_consistency(db, data.date, data.mileage_km, exclude_service_id=entry.id)
    exchange_rate = get_rate(db, data.currency)

    entry.date = data.date
    entry.mileage_km = data.mileage_km
    entry.type = data.type
    entry.description = data.description
    entry.cost = data.cost
    entry.currency = data.currency
    entry.exchange_rate = exchange_rate
    entry.notes = data.notes

    db.add(entry)
    db.commit()
    db.refresh(entry)
    recalculate_current_mileage(db)

    return _to_read(entry, _attachments_for(db, entry.id))


def delete_entry(db: Session, entry: ServiceEntry) -> None:
    db.delete(entry)
    db.commit()
    recalculate_current_mileage(db)


def list_entries(db: Session) -> list[ServiceEntryRead]:
    entries = db.exec(select(ServiceEntry).order_by(ServiceEntry.date.desc())).all()
    return [_to_read(entry, _attachments_for(db, entry.id)) for entry in entries]

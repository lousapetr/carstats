from sqlmodel import Session, select

from app.attachments.models import Attachment
from app.car.service import bump_current_mileage
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
        notes=entry.notes,
        attachments=[
            AttachmentRead(id=a.id, filename=a.filename, content_type=a.content_type)
            for a in attachments
        ],
    )


def create_entry(db: Session, data: ServiceEntryCreate) -> ServiceEntryRead:
    entry = ServiceEntry.model_validate(data)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    bump_current_mileage(db, entry.mileage_km)
    return _to_read(entry, [])


def delete_entry(db: Session, entry: ServiceEntry) -> None:
    db.delete(entry)
    db.commit()


def list_entries(db: Session) -> list[ServiceEntryRead]:
    entries = db.exec(select(ServiceEntry).order_by(ServiceEntry.date.desc())).all()
    results = []
    for entry in entries:
        attachments = db.exec(
            select(Attachment).where(Attachment.service_entry_id == entry.id)
        ).all()
        results.append(_to_read(entry, attachments))
    return results


def get_entry_with_attachments(db: Session, entry: ServiceEntry) -> ServiceEntryRead:
    attachments = db.exec(
        select(Attachment).where(Attachment.service_entry_id == entry.id)
    ).all()
    return _to_read(entry, attachments)

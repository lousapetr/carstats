from collections import defaultdict

from sqlmodel import Session, col, select

from app.attachments import storage
from app.attachments.models import Attachment, AttachmentRead
from app.car.service import (
    recalculate_current_mileage,
    validate_mileage_consistency,
)
from app.core.duplicates import DuplicateEntryError, czech_date, normalize_text
from app.currency.service import get_rate
from app.maintenance.models import ServiceEntry, ServiceEntryCreate, ServiceEntryRead


def _to_read(entry: ServiceEntry, attachments: list[Attachment]) -> ServiceEntryRead:
    assert entry.id is not None
    return ServiceEntryRead(
        id=entry.id,
        date=entry.date,
        mileage_km=entry.mileage_km,
        type=entry.type,
        description=entry.description,
        cost=entry.cost,
        currency=entry.currency,
        exchange_rate=entry.exchange_rate,
        cost_czk=round(entry.cost * entry.exchange_rate, 2),
        notes=entry.notes,
        attachments=[AttachmentRead.model_validate(a, from_attributes=True) for a in attachments],
    )


def _attachments_for(db: Session, entry: ServiceEntry) -> list[Attachment]:
    assert entry.id is not None
    return list(db.exec(select(Attachment).where(Attachment.service_entry_id == entry.id)).all())


def _ensure_not_duplicate(db: Session, data: ServiceEntryCreate, exclude_id: int | None) -> None:
    query = select(ServiceEntry).where(
        ServiceEntry.date == data.date,
        ServiceEntry.mileage_km == data.mileage_km,
        ServiceEntry.type == data.type,
    )
    if exclude_id is not None:
        query = query.where(col(ServiceEntry.id) != exclude_id)
    wanted = normalize_text(data.description)
    if any(normalize_text(e.description) == wanted for e in db.exec(query).all()):
        raise DuplicateEntryError(
            f"Stejný servisní záznam z {czech_date(data.date)} při {data.mileage_km:g} km"
            " už existuje."
        )


def create_entry(
    db: Session, data: ServiceEntryCreate, *, allow_duplicate: bool = False
) -> ServiceEntryRead:
    if not allow_duplicate:
        _ensure_not_duplicate(db, data, exclude_id=None)
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


def update_entry(
    db: Session, entry: ServiceEntry, data: ServiceEntryCreate, *, allow_duplicate: bool = False
) -> ServiceEntryRead:
    assert entry.id is not None
    if not allow_duplicate:
        _ensure_not_duplicate(db, data, exclude_id=entry.id)
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

    return _to_read(entry, _attachments_for(db, entry))


def delete_entry(db: Session, entry: ServiceEntry) -> None:
    assert entry.id is not None
    entry_id = entry.id
    for attachment in _attachments_for(db, entry):
        db.delete(attachment)
    db.delete(entry)
    db.commit()
    # Files go only after the commit, so a failed delete never leaves rows pointing at nothing.
    storage.delete_entry_dir(entry_id)
    recalculate_current_mileage(db)


def list_entries(db: Session) -> list[ServiceEntryRead]:
    entries = db.exec(
        select(ServiceEntry).order_by(
            col(ServiceEntry.mileage_km).desc(), col(ServiceEntry.id).desc()
        )
    ).all()
    # One query for all attachments rather than one per entry.
    entry_ids = [entry.id for entry in entries if entry.id is not None]
    by_entry: dict[int, list[Attachment]] = defaultdict(list)
    for attachment in db.exec(
        select(Attachment).where(col(Attachment.service_entry_id).in_(entry_ids))
    ).all():
        by_entry[attachment.service_entry_id].append(attachment)
    return [_to_read(entry, by_entry[entry.id]) for entry in entries if entry.id is not None]

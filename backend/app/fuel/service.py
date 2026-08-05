from sqlmodel import Session, select

from app.car.service import bump_current_mileage
from app.fuel.models import FuelEntry
from app.fuel.schemas import FuelEntryCreate, FuelEntryRead


def _to_read(entry: FuelEntry, consumption_l_per_100km: float | None) -> FuelEntryRead:
    return FuelEntryRead(
        id=entry.id,
        date=entry.date,
        mileage_km=entry.mileage_km,
        liters=entry.liters,
        price_total=entry.price_total,
        notes=entry.notes,
        price_per_liter=round(entry.price_total / entry.liters, 3) if entry.liters else 0,
        consumption_l_per_100km=consumption_l_per_100km,
    )


def create_entry(db: Session, data: FuelEntryCreate) -> FuelEntryRead:
    entry = FuelEntry.model_validate(data)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    bump_current_mileage(db, entry.mileage_km)

    previous = db.exec(
        select(FuelEntry)
        .where(FuelEntry.mileage_km < entry.mileage_km, FuelEntry.id != entry.id)
        .order_by(FuelEntry.mileage_km.desc())
    ).first()
    consumption = None
    if previous is not None:
        distance = entry.mileage_km - previous.mileage_km
        if distance > 0:
            consumption = round(entry.liters / distance * 100, 2)
    return _to_read(entry, consumption)


def delete_entry(db: Session, entry: FuelEntry) -> None:
    db.delete(entry)
    db.commit()


def list_entries_with_stats(db: Session) -> list[FuelEntryRead]:
    """Fuel entries ordered oldest-first, each annotated with derived
    price/liter and consumption since the previous fill-up (by mileage).
    """
    entries = db.exec(select(FuelEntry).order_by(FuelEntry.mileage_km)).all()
    results: list[FuelEntryRead] = []
    previous: FuelEntry | None = None
    for entry in entries:
        consumption = None
        if previous is not None:
            distance = entry.mileage_km - previous.mileage_km
            if distance > 0:
                consumption = round(entry.liters / distance * 100, 2)
        results.append(_to_read(entry, consumption))
        previous = entry
    # Return newest-first for display.
    return list(reversed(results))

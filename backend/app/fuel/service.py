from sqlmodel import Session, select

from app.car.service import (
    recalculate_current_mileage,
    validate_mileage_consistency,
)
from app.currency.service import get_rate
from app.fuel.models import FuelEntry
from app.fuel.schemas import FuelEntryCreate, FuelEntryRead


def _to_read(entry: FuelEntry, consumption_l_per_100km: float | None) -> FuelEntryRead:
    price_total = round(entry.liters * entry.price_per_liter, 2)
    return FuelEntryRead(
        id=entry.id,
        date=entry.date,
        mileage_km=entry.mileage_km,
        liters=entry.liters,
        price_per_liter=entry.price_per_liter,
        currency=entry.currency,
        notes=entry.notes,
        price_per_liter_czk=round(entry.price_per_liter * entry.exchange_rate, 3),
        price_total=price_total,
        price_total_czk=round(price_total * entry.exchange_rate, 2),
        consumption_l_per_100km=consumption_l_per_100km,
    )


def _consumption_since_previous(db: Session, entry: FuelEntry) -> float | None:
    previous = db.exec(
        select(FuelEntry)
        .where(FuelEntry.mileage_km < entry.mileage_km, FuelEntry.id != entry.id)
        .order_by(FuelEntry.mileage_km.desc())
    ).first()
    if previous is None:
        return None
    distance = entry.mileage_km - previous.mileage_km
    if distance <= 0:
        return None
    return round(entry.liters / distance * 100, 2)


def create_entry(db: Session, data: FuelEntryCreate) -> FuelEntryRead:
    validate_mileage_consistency(db, data.date, data.mileage_km)
    exchange_rate = get_rate(db, data.currency)

    entry = FuelEntry(
        date=data.date,
        mileage_km=data.mileage_km,
        liters=data.liters,
        price_per_liter=data.price_per_liter,
        currency=data.currency,
        exchange_rate=exchange_rate,
        notes=data.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    recalculate_current_mileage(db)

    return _to_read(entry, _consumption_since_previous(db, entry))


def update_entry(db: Session, entry: FuelEntry, data: FuelEntryCreate) -> FuelEntryRead:
    validate_mileage_consistency(db, data.date, data.mileage_km, exclude_fuel_id=entry.id)
    exchange_rate = get_rate(db, data.currency)

    entry.date = data.date
    entry.mileage_km = data.mileage_km
    entry.liters = data.liters
    entry.price_per_liter = data.price_per_liter
    entry.currency = data.currency
    entry.exchange_rate = exchange_rate
    entry.notes = data.notes

    db.add(entry)
    db.commit()
    db.refresh(entry)
    recalculate_current_mileage(db)

    return _to_read(entry, _consumption_since_previous(db, entry))


def delete_entry(db: Session, entry: FuelEntry) -> None:
    db.delete(entry)
    db.commit()
    recalculate_current_mileage(db)


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

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
        full_tank=entry.full_tank,
        notes=entry.notes,
        price_per_liter_czk=round(entry.price_per_liter * entry.exchange_rate, 3),
        price_total=price_total,
        price_total_czk=round(price_total * entry.exchange_rate, 2),
        consumption_l_per_100km=consumption_l_per_100km,
    )


def _compute_consumptions(entries_oldest_first: list[FuelEntry]) -> dict[int, float | None]:
    """Full-to-full accounting: consumption is only emitted on full-tank
    entries, as the liters bought since the previous full-tank entry
    (including this one) divided by the mileage delta between those two
    full-tank points. Partial fills in between just accumulate liters and
    emit no reading of their own, so one or more partials don't distort the
    number the way naive previous-entry deltas would.
    """
    consumptions: dict[int, float | None] = {}
    last_full: FuelEntry | None = None
    running_liters = 0.0
    for entry in entries_oldest_first:
        running_liters += entry.liters
        if not entry.full_tank:
            consumptions[entry.id] = None
            continue
        distance = entry.mileage_km - last_full.mileage_km if last_full else 0
        consumptions[entry.id] = (
            round(running_liters / distance * 100, 2) if last_full and distance > 0 else None
        )
        last_full = entry
        running_liters = 0.0
    return consumptions


def _consumption_for_entry(db: Session, entry: FuelEntry) -> float | None:
    entries = db.exec(select(FuelEntry).order_by(FuelEntry.mileage_km)).all()
    return _compute_consumptions(entries).get(entry.id)


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
        full_tank=data.full_tank,
        notes=data.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    recalculate_current_mileage(db)

    return _to_read(entry, _consumption_for_entry(db, entry))


def update_entry(db: Session, entry: FuelEntry, data: FuelEntryCreate) -> FuelEntryRead:
    validate_mileage_consistency(db, data.date, data.mileage_km, exclude_fuel_id=entry.id)
    exchange_rate = get_rate(db, data.currency)

    entry.date = data.date
    entry.mileage_km = data.mileage_km
    entry.liters = data.liters
    entry.price_per_liter = data.price_per_liter
    entry.currency = data.currency
    entry.exchange_rate = exchange_rate
    entry.full_tank = data.full_tank
    entry.notes = data.notes

    db.add(entry)
    db.commit()
    db.refresh(entry)
    recalculate_current_mileage(db)

    return _to_read(entry, _consumption_for_entry(db, entry))


def delete_entry(db: Session, entry: FuelEntry) -> None:
    db.delete(entry)
    db.commit()
    recalculate_current_mileage(db)


def list_entries_with_stats(db: Session) -> list[FuelEntryRead]:
    """Fuel entries ordered oldest-first, each annotated with derived
    price/liter and full-to-full consumption (see `_compute_consumptions`).
    """
    entries = db.exec(select(FuelEntry).order_by(FuelEntry.mileage_km)).all()
    consumptions = _compute_consumptions(entries)
    results = [_to_read(entry, consumptions[entry.id]) for entry in entries]
    # Return newest-first for display.
    return list(reversed(results))

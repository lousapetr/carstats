from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from sqlmodel import Session, col, select

from app.car.service import (
    recalculate_current_mileage,
    validate_mileage_consistency,
)
from app.core.duplicates import DuplicateEntryError, czech_date
from app.currency.service import get_rate
from app.fuel.models import FuelEntry, FuelEntryCreate, FuelEntryRead


def _to_read(entry: FuelEntry, consumption_l_per_100km: float | None) -> FuelEntryRead:
    price_total = (
        round(entry.liters * entry.price_per_liter, 2)
        if entry.liters is not None and entry.price_per_liter is not None
        else None
    )
    assert entry.id is not None
    return FuelEntryRead(
        id=entry.id,
        date=entry.date,
        mileage_km=entry.mileage_km,
        liters=entry.liters,
        price_per_liter=entry.price_per_liter,
        currency=entry.currency,
        exchange_rate=entry.exchange_rate,
        full_tank=entry.full_tank,
        notes=entry.notes,
        is_draft=entry.is_draft,
        price_per_liter_czk=(
            round(entry.price_per_liter * entry.exchange_rate, 3)
            if entry.price_per_liter is not None
            else None
        ),
        price_total=price_total,
        price_total_czk=(
            round(price_total * entry.exchange_rate, 2) if price_total is not None else None
        ),
        consumption_l_per_100km=consumption_l_per_100km,
    )


@dataclass(frozen=True)
class FullToFullInterval:
    """One measurable stretch between two full-tank fill-ups.

    `date` and `closing_entry_id` are the *closing* full tank's — the entry
    that carries this interval's consumption in `list_entries_with_stats`,
    and the one whose year the interval is counted under in per-year stats.
    """

    closing_entry_id: int
    date: date
    liters: float
    distance_km: float

    @property
    def consumption_l_per_100km(self) -> float:
        """Never None and never dividing by zero: an interval is only built
        once both ends are known and the mileage actually advanced.
        """
        return round(self.liters / self.distance_km * 100, 2)


def _mileage(entry: FuelEntry) -> float:
    assert entry.mileage_km is not None
    return entry.mileage_km


def full_to_full_intervals(entries: Sequence[FuelEntry]) -> list[FullToFullInterval]:
    """Full-to-full accounting: a measurable interval runs from one full-tank
    entry to the next, with the liters bought over it being everything since
    the previous full tank (the closing entry included). Partial fills in
    between only accumulate liters and close no interval of their own, so they
    don't distort the numbers the way naive previous-entry deltas would.

    Entries must be complete (non-draft) and may be passed in any order. The
    first full tank opens the first interval without closing one, so n full
    tanks yield at most n-1 intervals.
    """
    intervals: list[FullToFullInterval] = []
    last_full: FuelEntry | None = None
    running_liters = 0.0
    for entry in sorted(entries, key=_mileage):
        assert entry.id is not None and entry.liters is not None and entry.date is not None
        running_liters += entry.liters
        if not entry.full_tank:
            continue
        distance = _mileage(entry) - _mileage(last_full) if last_full else 0.0
        if last_full is not None and distance > 0:
            intervals.append(
                FullToFullInterval(
                    closing_entry_id=entry.id,
                    date=entry.date,
                    liters=running_liters,
                    distance_km=distance,
                )
            )
        last_full = entry
        running_liters = 0.0
    return intervals


def _compute_consumptions(entries: Sequence[FuelEntry]) -> dict[int, float | None]:
    """Per-entry consumption: set on the full-tank entry that closes a
    full-to-full interval, None everywhere else.
    """
    consumptions: dict[int, float | None] = {}
    for entry in entries:
        assert entry.id is not None
        consumptions[entry.id] = None
    for interval in full_to_full_intervals(entries):
        consumptions[interval.closing_entry_id] = interval.consumption_l_per_100km
    return consumptions


def _entries_oldest_first(db: Session) -> Sequence[FuelEntry]:
    """Complete (non-draft) entries only; drafts take no part in consumption."""
    return db.exec(
        select(FuelEntry)
        .where(col(FuelEntry.is_draft).is_(False))
        .order_by(col(FuelEntry.mileage_km), col(FuelEntry.id))
    ).all()


def _consumption_for_entry(db: Session, entry: FuelEntry) -> float | None:
    assert entry.id is not None
    entries = _entries_oldest_first(db)
    return _compute_consumptions(entries).get(entry.id)


def _ensure_not_duplicate(
    db: Session, entry_date: date, mileage_km: float, exclude_id: int | None
) -> None:
    query = select(FuelEntry).where(
        FuelEntry.date == entry_date,
        FuelEntry.mileage_km == mileage_km,
        col(FuelEntry.is_draft).is_(False),
    )
    if exclude_id is not None:
        query = query.where(col(FuelEntry.id) != exclude_id)
    if db.exec(query).first() is not None:
        raise DuplicateEntryError(
            f"Tankování z {czech_date(entry_date)} při {mileage_km:g} km už je zapsané."
        )


def _validate_complete(
    db: Session, data: FuelEntryCreate, *, allow_duplicate: bool, exclude_id: int | None
) -> None:
    """Duplicate and mileage checks for a non-draft save; a draft skips both."""
    if data.is_draft:
        return
    assert data.date is not None and data.mileage_km is not None
    if not allow_duplicate:
        _ensure_not_duplicate(db, data.date, data.mileage_km, exclude_id)
    validate_mileage_consistency(db, data.date, data.mileage_km, exclude_fuel_id=exclude_id)


def create_entry(
    db: Session, data: FuelEntryCreate, *, allow_duplicate: bool = False
) -> FuelEntryRead:
    _validate_complete(db, data, allow_duplicate=allow_duplicate, exclude_id=None)
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
        is_draft=data.is_draft,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    recalculate_current_mileage(db)

    return _to_read(entry, _consumption_for_entry(db, entry))


def update_entry(
    db: Session, entry: FuelEntry, data: FuelEntryCreate, *, allow_duplicate: bool = False
) -> FuelEntryRead:
    _validate_complete(db, data, allow_duplicate=allow_duplicate, exclude_id=entry.id)
    exchange_rate = get_rate(db, data.currency)

    entry.date = data.date
    entry.mileage_km = data.mileage_km
    entry.liters = data.liters
    entry.price_per_liter = data.price_per_liter
    entry.currency = data.currency
    entry.exchange_rate = exchange_rate
    entry.full_tank = data.full_tank
    entry.notes = data.notes
    entry.is_draft = data.is_draft

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
    """Drafts first (newest-created first), then complete entries newest-first
    by mileage, each annotated with derived price/liter and full-to-full
    consumption (see `_compute_consumptions`). Drafts carry no consumption.
    """
    drafts = db.exec(
        select(FuelEntry)
        .where(col(FuelEntry.is_draft).is_(True))
        .order_by(col(FuelEntry.created_at).desc(), col(FuelEntry.id).desc())
    ).all()
    entries = _entries_oldest_first(db)
    consumptions = _compute_consumptions(entries)
    results: list[FuelEntryRead] = []
    for entry in entries:
        assert entry.id is not None
        results.append(_to_read(entry, consumptions[entry.id]))
    # Complete entries newest-first for display.
    return [_to_read(d, None) for d in drafts] + list(reversed(results))

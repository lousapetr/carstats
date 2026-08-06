from datetime import date as date_type

from sqlmodel import Session, func, select

from app.car.models import CarProfile


def get_or_create_profile(db: Session) -> CarProfile:
    profile = db.exec(select(CarProfile)).first()
    if profile is None:
        profile = CarProfile()
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def recalculate_current_mileage(db: Session) -> None:
    """Recompute CarProfile.current_mileage_km as the max across all fuel/service
    entries, so edits and deletes of the highest-mileage entry stay correct
    (a plain monotonic "bump" would leave stale data behind).
    """
    from app.fuel.models import FuelEntry
    from app.maintenance.models import ServiceEntry

    fuel_max = db.exec(select(func.max(FuelEntry.mileage_km))).first()
    service_max = db.exec(select(func.max(ServiceEntry.mileage_km))).first()
    candidates = [m for m in (fuel_max, service_max) if m is not None]

    profile = get_or_create_profile(db)
    profile.current_mileage_km = max(candidates) if candidates else 0
    db.add(profile)
    db.commit()


def validate_mileage_consistency(
    db: Session,
    entry_date: date_type,
    mileage_km: float,
    *,
    exclude_fuel_id: int | None = None,
    exclude_service_id: int | None = None,
) -> None:
    """Typo protection: a new/edited entry's mileage must sit between the
    neighboring entries by date (across both fuel and service history),
    while still allowing historical backfill out of upload order.
    """
    from app.fuel.models import FuelEntry
    from app.maintenance.models import ServiceEntry

    fuel_entries = db.exec(select(FuelEntry)).all()
    service_entries = db.exec(select(ServiceEntry)).all()

    points = [(e.date, e.mileage_km) for e in fuel_entries if e.id != exclude_fuel_id] + [
        (e.date, e.mileage_km) for e in service_entries if e.id != exclude_service_id
    ]

    before = [m for d, m in points if d < entry_date]
    after = [m for d, m in points if d > entry_date]

    if before and mileage_km < max(before):
        raise ValueError(
            f"Mileage ({mileage_km:g} km) is lower than a previous entry "
            f"({max(before):g} km)"
        )
    if after and mileage_km > min(after):
        raise ValueError(
            f"Mileage ({mileage_km:g} km) is higher than a later entry "
            f"({min(after):g} km)"
        )

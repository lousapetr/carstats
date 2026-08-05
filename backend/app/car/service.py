from sqlmodel import Session, select

from app.car.models import CarProfile


def get_or_create_profile(db: Session) -> CarProfile:
    profile = db.exec(select(CarProfile)).first()
    if profile is None:
        profile = CarProfile()
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def bump_current_mileage(db: Session, mileage_km: float) -> None:
    """Keep CarProfile.current_mileage_km in sync with the latest logged entry."""
    profile = get_or_create_profile(db)
    if mileage_km > profile.current_mileage_km:
        profile.current_mileage_km = mileage_km
        db.add(profile)
        db.commit()

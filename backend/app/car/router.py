from fastapi import APIRouter

from app.car import service
from app.car.models import CarProfile
from app.car.schemas import CarProfileRead, CarProfileUpdate
from app.core.database import DbSession
from app.core.security import CurrentUser

router = APIRouter(prefix="/car", tags=["car"])


@router.get("", response_model=CarProfileRead)
def get_car_profile(user: CurrentUser, db: DbSession) -> CarProfile:
    return service.get_or_create_profile(db)


@router.put("", response_model=CarProfileRead)
def update_car_profile(data: CarProfileUpdate, user: CurrentUser, db: DbSession) -> CarProfile:
    profile = service.get_or_create_profile(db)
    profile.name = data.name
    profile.make = data.make
    profile.model = data.model
    profile.year = data.year
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

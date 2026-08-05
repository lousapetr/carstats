from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_db
from app.core.security import CurrentUser
from app.fuel import service
from app.fuel.models import FuelEntry
from app.fuel.schemas import FuelEntryCreate, FuelEntryRead

router = APIRouter(prefix="/fuel-entries", tags=["fuel"])


@router.get("", response_model=list[FuelEntryRead])
def list_fuel_entries(user: CurrentUser, db: Session = Depends(get_db)) -> list[FuelEntryRead]:
    return service.list_entries_with_stats(db)


@router.post("", response_model=FuelEntryRead, status_code=status.HTTP_201_CREATED)
def create_fuel_entry(
    data: FuelEntryCreate, user: CurrentUser, db: Session = Depends(get_db)
) -> FuelEntryRead:
    return service.create_entry(db, data)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fuel_entry(entry_id: int, user: CurrentUser, db: Session = Depends(get_db)) -> None:
    entry = db.get(FuelEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Fuel entry not found")
    service.delete_entry(db, entry)

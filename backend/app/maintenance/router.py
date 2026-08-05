from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_db
from app.core.security import CurrentUser
from app.maintenance import service
from app.maintenance.models import ServiceEntry
from app.maintenance.schemas import ServiceEntryCreate, ServiceEntryRead

router = APIRouter(prefix="/service-entries", tags=["maintenance"])


@router.get("", response_model=list[ServiceEntryRead])
def list_service_entries(
    user: CurrentUser, db: Session = Depends(get_db)
) -> list[ServiceEntryRead]:
    return service.list_entries(db)


@router.post("", response_model=ServiceEntryRead, status_code=status.HTTP_201_CREATED)
def create_service_entry(
    data: ServiceEntryCreate, user: CurrentUser, db: Session = Depends(get_db)
) -> ServiceEntryRead:
    return service.create_entry(db, data)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service_entry(
    entry_id: int, user: CurrentUser, db: Session = Depends(get_db)
) -> None:
    entry = db.get(ServiceEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Service entry not found")
    service.delete_entry(db, entry)

from fastapi import APIRouter, HTTPException, status

from app.core.database import DbSession
from app.core.duplicates import DuplicateEntryError
from app.core.security import CurrentUser
from app.maintenance import service
from app.maintenance.models import ServiceEntry, ServiceEntryCreate, ServiceEntryRead

router = APIRouter(prefix="/service-entries", tags=["maintenance"])


@router.get("", response_model=list[ServiceEntryRead])
def list_service_entries(user: CurrentUser, db: DbSession) -> list[ServiceEntryRead]:
    return service.list_entries(db)


@router.post("", response_model=ServiceEntryRead, status_code=status.HTTP_201_CREATED)
def create_service_entry(
    data: ServiceEntryCreate, user: CurrentUser, db: DbSession, force: bool = False
) -> ServiceEntryRead:
    try:
        return service.create_entry(db, data, allow_duplicate=force)
    except DuplicateEntryError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{entry_id}", response_model=ServiceEntryRead)
def update_service_entry(
    entry_id: int,
    data: ServiceEntryCreate,
    user: CurrentUser,
    db: DbSession,
    force: bool = False,
) -> ServiceEntryRead:
    entry = db.get(ServiceEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Service entry not found")
    try:
        return service.update_entry(db, entry, data, allow_duplicate=force)
    except DuplicateEntryError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service_entry(entry_id: int, user: CurrentUser, db: DbSession) -> None:
    entry = db.get(ServiceEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Service entry not found")
    service.delete_entry(db, entry)

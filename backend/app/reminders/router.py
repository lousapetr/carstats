from fastapi import APIRouter, HTTPException, status
from sqlmodel import Session

from app.core.database import DbSession
from app.core.duplicates import DuplicateEntryError
from app.core.security import CurrentUser
from app.reminders import service
from app.reminders.models import Reminder, ReminderCreate, ReminderRead

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("", response_model=list[ReminderRead])
def list_reminders(user: CurrentUser, db: DbSession) -> list[ReminderRead]:
    return service.list_active_reminders(db)


@router.post("", response_model=ReminderRead, status_code=status.HTTP_201_CREATED)
def create_reminder(
    data: ReminderCreate, user: CurrentUser, db: DbSession, force: bool = False
) -> ReminderRead:
    try:
        return service.create_reminder(db, data, allow_duplicate=force)
    except DuplicateEntryError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def _get_or_404(db: Session, reminder_id: int) -> Reminder:
    reminder = db.get(Reminder, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder


@router.put("/{reminder_id}", response_model=ReminderRead)
def update_reminder(
    reminder_id: int, data: ReminderCreate, user: CurrentUser, db: DbSession, force: bool = False
) -> ReminderRead:
    reminder = _get_or_404(db, reminder_id)
    try:
        return service.update_reminder(db, reminder, data, allow_duplicate=force)
    except DuplicateEntryError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{reminder_id}/complete", response_model=ReminderRead)
def complete_reminder(reminder_id: int, user: CurrentUser, db: DbSession) -> ReminderRead:
    reminder = _get_or_404(db, reminder_id)
    return service.complete_reminder(db, reminder)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(reminder_id: int, user: CurrentUser, db: DbSession) -> None:
    reminder = _get_or_404(db, reminder_id)
    service.delete_reminder(db, reminder)

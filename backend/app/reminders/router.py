from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_db
from app.core.security import CurrentUser
from app.reminders import service
from app.reminders.models import Reminder
from app.reminders.schemas import ReminderCreate, ReminderRead

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("", response_model=list[ReminderRead])
def list_reminders(user: CurrentUser, db: Session = Depends(get_db)) -> list[ReminderRead]:
    return service.list_active_reminders(db)


@router.post("", response_model=ReminderRead, status_code=status.HTTP_201_CREATED)
def create_reminder(
    data: ReminderCreate, user: CurrentUser, db: Session = Depends(get_db)
) -> ReminderRead:
    return service.create_reminder(db, data)


def _get_or_404(db: Session, reminder_id: int) -> Reminder:
    reminder = db.get(Reminder, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder


@router.put("/{reminder_id}", response_model=ReminderRead)
def update_reminder(
    reminder_id: int, data: ReminderCreate, user: CurrentUser, db: Session = Depends(get_db)
) -> ReminderRead:
    reminder = _get_or_404(db, reminder_id)
    return service.update_reminder(db, reminder, data)


@router.post("/{reminder_id}/complete", response_model=ReminderRead)
def complete_reminder(
    reminder_id: int, user: CurrentUser, db: Session = Depends(get_db)
) -> ReminderRead:
    reminder = _get_or_404(db, reminder_id)
    return service.complete_reminder(db, reminder)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(reminder_id: int, user: CurrentUser, db: Session = Depends(get_db)) -> None:
    reminder = _get_or_404(db, reminder_id)
    service.delete_reminder(db, reminder)

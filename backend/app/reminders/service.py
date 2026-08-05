from datetime import UTC, date, datetime

from sqlmodel import Session, select

from app.car.service import get_or_create_profile
from app.reminders.models import Reminder
from app.reminders.schemas import ReminderCreate, ReminderRead, ReminderStatus

DUE_SOON_DAYS = 14
DUE_SOON_KM = 500


def compute_status(reminder: Reminder, current_mileage_km: float, today: date) -> ReminderStatus:
    overdue = False
    due_soon = False

    if reminder.due_date is not None:
        if reminder.due_date < today:
            overdue = True
        elif (reminder.due_date - today).days <= DUE_SOON_DAYS:
            due_soon = True

    if reminder.due_mileage_km is not None:
        if current_mileage_km >= reminder.due_mileage_km:
            overdue = True
        elif reminder.due_mileage_km - current_mileage_km <= DUE_SOON_KM:
            due_soon = True

    if overdue:
        return "overdue"
    if due_soon:
        return "due_soon"
    return "ok"


_STATUS_RANK = {"overdue": 0, "due_soon": 1, "ok": 2}


def _to_read(reminder: Reminder, current_mileage_km: float, today: date) -> ReminderRead:
    return ReminderRead(
        id=reminder.id,
        title=reminder.title,
        notes=reminder.notes,
        due_date=reminder.due_date,
        due_mileage_km=reminder.due_mileage_km,
        recurrence_days=reminder.recurrence_days,
        recurrence_km=reminder.recurrence_km,
        completed_at=reminder.completed_at,
        status=compute_status(reminder, current_mileage_km, today),
    )


def list_active_reminders(db: Session) -> list[ReminderRead]:
    current_mileage_km = get_or_create_profile(db).current_mileage_km
    today = date.today()
    reminders = db.exec(select(Reminder).where(Reminder.completed_at.is_(None))).all()
    reads = [_to_read(r, current_mileage_km, today) for r in reminders]
    reads.sort(key=lambda r: _STATUS_RANK[r.status])
    return reads


def create_reminder(db: Session, data: ReminderCreate) -> ReminderRead:
    reminder = Reminder.model_validate(data)
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    profile = get_or_create_profile(db)
    return _to_read(reminder, profile.current_mileage_km, date.today())


def complete_reminder(db: Session, reminder: Reminder) -> ReminderRead:
    """Mark done. If the reminder recurs, roll it forward instead of hiding it."""
    if reminder.recurrence_days is not None and reminder.due_date is not None:
        base = max(reminder.due_date, date.today())
        reminder.due_date = base.fromordinal(base.toordinal() + reminder.recurrence_days)
    if reminder.recurrence_km is not None and reminder.due_mileage_km is not None:
        profile = get_or_create_profile(db)
        base_mileage = max(reminder.due_mileage_km, profile.current_mileage_km)
        reminder.due_mileage_km = base_mileage + reminder.recurrence_km

    is_recurring = reminder.recurrence_days is not None or reminder.recurrence_km is not None
    reminder.completed_at = None if is_recurring else datetime.now(UTC)

    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    profile = get_or_create_profile(db)
    return _to_read(reminder, profile.current_mileage_km, date.today())


def delete_reminder(db: Session, reminder: Reminder) -> None:
    db.delete(reminder)
    db.commit()

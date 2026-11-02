from datetime import UTC, date, datetime, timedelta

from sqlmodel import Session, col, select

from app.car.service import get_or_create_profile
from app.core.duplicates import DuplicateEntryError, normalize_text
from app.reminders.models import Reminder, ReminderCreate, ReminderRead, ReminderStatus

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
    assert reminder.id is not None
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
    reminders = db.exec(select(Reminder).where(col(Reminder.completed_at).is_(None))).all()
    reads = [_to_read(r, current_mileage_km, today) for r in reminders]
    reads.sort(key=lambda r: _STATUS_RANK[r.status])
    return reads


def _ensure_not_duplicate(db: Session, data: ReminderCreate, exclude_id: int | None) -> None:
    # `== None` never matches in SQL, so a missing field needs IS NULL.
    due_date = col(Reminder.due_date)
    due_km = col(Reminder.due_mileage_km)
    query = select(Reminder).where(
        col(Reminder.completed_at).is_(None),
        due_date.is_(None) if data.due_date is None else due_date == data.due_date,
        due_km.is_(None) if data.due_mileage_km is None else due_km == data.due_mileage_km,
    )
    if exclude_id is not None:
        query = query.where(col(Reminder.id) != exclude_id)
    wanted = normalize_text(data.title)
    if any(normalize_text(r.title) == wanted for r in db.exec(query).all()):
        raise DuplicateEntryError(
            f"Aktivní připomínka „{data.title.strip()}“ se stejným termínem už existuje."
        )


def create_reminder(
    db: Session, data: ReminderCreate, *, allow_duplicate: bool = False
) -> ReminderRead:
    if not allow_duplicate:
        _ensure_not_duplicate(db, data, exclude_id=None)
    reminder = Reminder.model_validate(data)
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    profile = get_or_create_profile(db)
    return _to_read(reminder, profile.current_mileage_km, date.today())


def update_reminder(
    db: Session, reminder: Reminder, data: ReminderCreate, *, allow_duplicate: bool = False
) -> ReminderRead:
    if not allow_duplicate:
        _ensure_not_duplicate(db, data, exclude_id=reminder.id)
    reminder.title = data.title
    reminder.notes = data.notes
    reminder.due_date = data.due_date
    reminder.due_mileage_km = data.due_mileage_km
    reminder.recurrence_days = data.recurrence_days
    reminder.recurrence_km = data.recurrence_km

    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    profile = get_or_create_profile(db)
    return _to_read(reminder, profile.current_mileage_km, date.today())


def complete_reminder(db: Session, reminder: Reminder) -> ReminderRead:
    """Mark done. If the reminder recurs, roll it forward instead of hiding it.

    A recurrence with no due field yet (the form allows it) still rolls
    forward, seeded from today / the current mileage — otherwise "Hotovo"
    would be a no-op and the reminder could never leave the active list.
    """
    rolled = False
    if reminder.recurrence_days is not None:
        base = max(reminder.due_date, date.today()) if reminder.due_date else date.today()
        reminder.due_date = base + timedelta(days=reminder.recurrence_days)
        rolled = True
    if reminder.recurrence_km is not None:
        profile = get_or_create_profile(db)
        base_mileage = max(reminder.due_mileage_km or 0, profile.current_mileage_km)
        reminder.due_mileage_km = base_mileage + reminder.recurrence_km
        rolled = True

    reminder.completed_at = None if rolled else datetime.now(UTC)

    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    profile = get_or_create_profile(db)
    return _to_read(reminder, profile.current_mileage_km, date.today())


def delete_reminder(db: Session, reminder: Reminder) -> None:
    db.delete(reminder)
    db.commit()

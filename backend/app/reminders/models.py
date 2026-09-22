from datetime import UTC, date, datetime
from typing import Literal

from sqlmodel import Field, SQLModel

ReminderStatus = Literal["ok", "due_soon", "overdue"]


class ReminderBase(SQLModel):
    title: str
    notes: str | None = None

    due_date: date | None = None
    due_mileage_km: float | None = None

    # If set, completing this reminder schedules the next occurrence
    # instead of just marking it done.
    recurrence_days: int | None = None
    recurrence_km: float | None = None


class Reminder(ReminderBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReminderCreate(ReminderBase):
    pass


class ReminderRead(ReminderBase):
    id: int
    completed_at: datetime | None
    status: ReminderStatus

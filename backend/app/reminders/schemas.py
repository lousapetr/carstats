from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

ReminderStatus = Literal["ok", "due_soon", "overdue"]


class ReminderCreate(BaseModel):
    title: str
    notes: str | None = None
    due_date: date | None = None
    due_mileage_km: float | None = None
    recurrence_days: int | None = None
    recurrence_km: float | None = None


class ReminderRead(ReminderCreate):
    id: int
    completed_at: datetime | None
    status: ReminderStatus

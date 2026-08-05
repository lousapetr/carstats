from datetime import UTC, date, datetime

from sqlmodel import Field, SQLModel


class Reminder(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    notes: str | None = None

    due_date: date | None = None
    due_mileage_km: float | None = None

    # If set, completing this reminder schedules the next occurrence
    # instead of just marking it done.
    recurrence_days: int | None = None
    recurrence_km: float | None = None

    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

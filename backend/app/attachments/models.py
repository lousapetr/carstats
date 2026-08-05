from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Attachment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    service_entry_id: int = Field(foreign_key="serviceentry.id")
    filename: str
    content_type: str
    path: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

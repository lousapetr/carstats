from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class AttachmentBase(SQLModel):
    filename: str
    content_type: str


class Attachment(AttachmentBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    service_entry_id: int = Field(foreign_key="serviceentry.id")
    path: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AttachmentRead(AttachmentBase):
    id: int

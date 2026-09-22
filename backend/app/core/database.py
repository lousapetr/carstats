from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


DbSession = Annotated[Session, Depends(get_db)]


def create_db_and_tables() -> None:
    """Only for local dev/tests without running Alembic. Production uses migrations."""
    SQLModel.metadata.create_all(engine)

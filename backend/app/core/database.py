import sqlite3
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine, event
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings


def enable_sqlite_foreign_keys(engine: Engine) -> None:
    """SQLite ships with FK enforcement off per connection; turn it on for this engine.

    Deliberately not a global listener: Alembic's own engine must keep it off,
    since batch migrations recreate tables by dropping them.
    """
    if engine.dialect.name != "sqlite":
        return

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_connection: sqlite3.Connection, _connection_record: object) -> None:
        _ = dbapi_connection.execute("PRAGMA foreign_keys=ON")


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
enable_sqlite_foreign_keys(engine)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


DbSession = Annotated[Session, Depends(get_db)]


def create_db_and_tables() -> None:
    """Only for local dev/tests without running Alembic. Production uses migrations."""
    SQLModel.metadata.create_all(engine)

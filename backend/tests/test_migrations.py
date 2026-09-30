from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine
from sqlmodel import SQLModel

from alembic import command
from app.core.config import settings

BACKEND_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture
def migrated_db_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    # env.py reads the URL from settings; no ini file so fileConfig() leaves logging alone.
    monkeypatch.setattr(settings, "database_url", url)
    config = Config()
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(config, "head")
    return url


def test_migrations_match_models(migrated_db_url: str) -> None:
    engine = create_engine(migrated_db_url)
    with engine.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), SQLModel.metadata)
    engine.dispose()
    assert diff == []

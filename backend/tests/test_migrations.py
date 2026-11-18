from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text
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


def test_draft_downgrade_deletes_drafts_and_their_files(
    migrated_db_url: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    uploads = tmp_path / "uploads"
    monkeypatch.setattr(settings, "uploads_dir", str(uploads))
    for entry_id in (1, 2):
        (uploads / str(entry_id)).mkdir(parents=True)
        (uploads / str(entry_id) / "f.pdf").write_bytes(b"x")
    engine = create_engine(migrated_db_url)
    with engine.begin() as connection:
        for entry_id, is_draft in ((1, True), (2, False)):
            connection.execute(
                text(
                    "INSERT INTO serviceentry (id, date, mileage_km, type, cost, currency,"
                    " exchange_rate, created_at, is_draft)"
                    " VALUES (:id, '2026-08-01', 1000, 'other', 5, 'CZK', 1, '2026-08-01', :d)"
                ),
                {"id": entry_id, "d": is_draft},
            )
            connection.execute(
                text(
                    "INSERT INTO attachment (service_entry_id, filename, content_type, path,"
                    " uploaded_at) VALUES (:id, 'f.pdf', 'application/pdf', :p, '2026-08-01')"
                ),
                {"id": entry_id, "p": f"{entry_id}/f.pdf"},
            )
    engine.dispose()

    config = Config()
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.downgrade(config, "0add10e08f48")

    engine = create_engine(migrated_db_url)
    with engine.connect() as connection:
        ids = connection.execute(text("SELECT id FROM serviceentry")).scalars().all()
        attached = connection.execute(text("SELECT service_entry_id FROM attachment")).all()
    engine.dispose()
    assert ids == [2]
    assert [row[0] for row in attached] == [2]
    assert not (uploads / "1").exists()
    assert (uploads / "2" / "f.pdf").exists()

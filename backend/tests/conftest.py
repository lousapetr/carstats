import os
import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

# Import every model module so SQLModel.metadata is fully populated.
from app.attachments import models as _attachments_models  # noqa: F401
from app.car import models as _car_models  # noqa: F401
from app.core.database import get_db
from app.core.security import get_current_user_email
from app.currency import models as _currency_models  # noqa: F401
from app.fuel import models as _fuel_models  # noqa: F401
from app.maintenance import models as _maintenance_models  # noqa: F401
from app.reminders import models as _reminders_models  # noqa: F401

# Every test that resolves a non-CZK exchange rate would otherwise trigger a
# real network call to the ČNB (see currency/service.py::_ensure_rates_fresh)
# on a fresh temp DB. Stub it to a fixed sample so tests stay offline and
# deterministic; EUR is 25.0 (not the 25.20 default) to match the rate
# values existing tests already assert on.
CNB_SAMPLE_TEXT = """05.09.2026 #172
Country|Currency|Amount|Code|Rate
EMU|euro|1|EUR|25.0
Poland|zloty|1|PLN|5.85
Hungary|forint|100|HUF|6.35
United Kingdom|pound|1|GBP|29.80
Switzerland|franc|1|CHF|27.00
Sweden|krona|1|SEK|2.20
Norway|krone|1|NOK|2.10
Denmark|krone|1|DKK|3.38
Romania|leu|1|RON|5.05
"""


@pytest.fixture(autouse=True)
def _stub_cnb_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.currency.cnb_client.fetch_daily_text", lambda: CNB_SAMPLE_TEXT)


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    def override_get_db() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    from app.main import app

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_email] = lambda: "test@example.com"

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    os.close(db_fd)
    os.remove(db_path)


@pytest.fixture()
def anon_client() -> Generator[TestClient, None, None]:
    """A client with no authenticated user, for testing the 401 path."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    def override_get_db() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    from app.main import app

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    os.close(db_fd)
    os.remove(db_path)

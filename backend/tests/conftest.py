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
from app.fuel import models as _fuel_models  # noqa: F401
from app.maintenance import models as _maintenance_models  # noqa: F401
from app.reminders import models as _reminders_models  # noqa: F401


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

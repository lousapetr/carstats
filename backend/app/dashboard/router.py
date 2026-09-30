from typing import Annotated

from fastapi import APIRouter, Query

from app.core.database import DbSession
from app.core.security import CurrentUser
from app.dashboard import service
from app.dashboard.periods import PERIOD_PATTERN
from app.dashboard.schemas import Dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=Dashboard)
def dashboard(
    user: CurrentUser,
    db: DbSession,
    period: Annotated[str, Query(pattern=PERIOD_PATTERN)] = "all",
) -> Dashboard:
    return service.get_dashboard(db, period)

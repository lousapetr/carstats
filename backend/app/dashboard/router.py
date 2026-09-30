from typing import Annotated

from fastapi import APIRouter, Query

from app.core.database import DbSession
from app.core.security import CurrentUser
from app.dashboard import service
from app.dashboard.periods import PERIOD_PATTERN
from app.dashboard.schemas import CostBreakdown, Dashboard, DashboardSummary, FuelTrendPoint

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=Dashboard)
def dashboard(
    user: CurrentUser,
    db: DbSession,
    period: Annotated[str, Query(pattern=PERIOD_PATTERN)] = "all",
) -> Dashboard:
    return service.get_dashboard(db, period)


@router.get("/summary", response_model=DashboardSummary)
def summary(user: CurrentUser, db: DbSession) -> DashboardSummary:
    return service.get_summary(db)


@router.get("/fuel-trend", response_model=list[FuelTrendPoint])
def fuel_trend(user: CurrentUser, db: DbSession) -> list[FuelTrendPoint]:
    return service.get_fuel_trend(db)


@router.get("/cost-breakdown", response_model=CostBreakdown)
def cost_breakdown(user: CurrentUser, db: DbSession) -> CostBreakdown:
    return service.get_cost_breakdown(db)

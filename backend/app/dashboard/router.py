from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_db
from app.core.security import CurrentUser
from app.dashboard import service
from app.dashboard.schemas import CostBreakdown, DashboardSummary, FuelTrendPoint

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(user: CurrentUser, db: Session = Depends(get_db)) -> DashboardSummary:
    return service.get_summary(db)


@router.get("/fuel-trend", response_model=list[FuelTrendPoint])
def fuel_trend(user: CurrentUser, db: Session = Depends(get_db)) -> list[FuelTrendPoint]:
    return service.get_fuel_trend(db)


@router.get("/cost-breakdown", response_model=CostBreakdown)
def cost_breakdown(user: CurrentUser, db: Session = Depends(get_db)) -> CostBreakdown:
    return service.get_cost_breakdown(db)

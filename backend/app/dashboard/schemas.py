from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.car.models import CarProfileRead
from app.maintenance.models import ServiceType
from app.reminders.models import ReminderRead


class FuelTimelineItem(BaseModel):
    date: date
    kind: Literal["fuel"] = "fuel"
    cost: float
    liters: float


class ServiceTimelineItem(BaseModel):
    date: date
    kind: Literal["service"] = "service"
    cost: float
    service_type: ServiceType
    description: str | None


TimelineItem = FuelTimelineItem | ServiceTimelineItem


class DashboardSummary(BaseModel):
    """All monetary fields are CZK-converted, regardless of the original
    currency each entry was logged in — the dashboard is always shown in Kč.
    """

    car: CarProfileRead
    total_fuel_cost: float
    total_fuel_liters: float
    total_fuel_entries: int
    total_maintenance_cost: float
    total_maintenance_entries: int
    total_cost: float
    total_cost_this_year: float
    total_cost_last_year: float
    cost_per_km: float | None
    # Distance-weighted over full-to-full intervals; the per-year figures cover
    # the intervals closed in that year, and are None when there are none.
    avg_consumption_l_per_100km: float | None
    avg_consumption_l_per_100km_this_year: float | None
    avg_consumption_l_per_100km_last_year: float | None
    upcoming_reminders: list[ReminderRead]
    recent_activity: list[TimelineItem]


class FuelTrendPoint(BaseModel):
    """price_total/price_per_liter are CZK-converted."""

    date: date
    price_total: float
    liters: float
    price_per_liter: float
    consumption_l_per_100km: float | None


class CostBreakdown(BaseModel):
    """Amounts are CZK-converted."""

    fuel_total: float
    maintenance_by_type: dict[str, float]

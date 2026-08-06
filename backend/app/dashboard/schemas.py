from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.reminders.schemas import ReminderRead


class CarSummary(BaseModel):
    name: str
    make: str
    model: str
    year: int | None
    current_mileage_km: float


class TimelineItem(BaseModel):
    date: date
    kind: Literal["fuel", "service"]
    label: str
    cost: float


class DashboardSummary(BaseModel):
    """All monetary fields are CZK-converted, regardless of the original
    currency each entry was logged in — the dashboard is always shown in Kč.
    """

    car: CarSummary
    total_fuel_cost: float
    total_fuel_liters: float
    total_fuel_entries: int
    total_maintenance_cost: float
    total_maintenance_entries: int
    total_cost: float
    total_cost_this_year: float
    total_cost_last_year: float
    cost_per_km: float | None
    avg_consumption_l_per_100km: float | None
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

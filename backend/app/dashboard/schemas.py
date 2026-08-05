from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.reminders.schemas import ReminderRead


class CarSummary(BaseModel):
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
    car: CarSummary
    total_fuel_cost: float
    total_fuel_liters: float
    total_fuel_entries: int
    total_maintenance_cost: float
    total_maintenance_entries: int
    total_cost: float
    avg_consumption_l_per_100km: float | None
    upcoming_reminders: list[ReminderRead]
    recent_activity: list[TimelineItem]


class FuelTrendPoint(BaseModel):
    date: date
    price_total: float
    liters: float
    price_per_liter: float
    consumption_l_per_100km: float | None


class CostBreakdown(BaseModel):
    fuel_total: float
    maintenance_by_type: dict[str, float]

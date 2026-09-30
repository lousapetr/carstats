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
    price_per_liter: float  # CZK-converted, like cost


class ServiceTimelineItem(BaseModel):
    date: date
    kind: Literal["service"] = "service"
    cost: float
    service_type: ServiceType
    description: str | None


TimelineItem = FuelTimelineItem | ServiceTimelineItem


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


class PeriodInfo(BaseModel):
    """The resolved `period`. Labels are left to the frontend, which composes
    them from the key and these dates; every bound is inclusive and None means
    unbounded.
    """

    key: str
    start: date | None
    end: date | None
    previous_start: date | None
    previous_end: date | None


class CostTotals(BaseModel):
    """CZK-converted costs and entry counts over one window."""

    fuel: float
    fuel_liters: float
    fuel_entries: int
    maintenance: float
    maintenance_entries: int
    total: float


class MonthlyCostPoint(BaseModel):
    """`bucket` is `YYYY-MM` for month granularity, `YYYY` for year."""

    bucket: str
    fuel: float
    service: float


class Dashboard(BaseModel):
    """Everything the dashboard shows, scoped to one period.

    Costs are filtered by entry date. Consumption is not: full-to-full
    intervals are computed over the whole fuel history and then filtered by
    the date of the full tank that *closes* each one, so an interval belongs
    wholly to the period it ended in — matching where its figure shows in the
    fuel log — and one straddling the window start is neither lost nor
    understated.

    `car` and `upcoming_reminders` are deliberately not period-scoped: the
    odometer is a fact about now and a reminder is about the future.
    """

    period: PeriodInfo
    available_years: list[int]
    car: CarProfileRead
    totals: CostTotals
    previous_totals: CostTotals | None
    # None when there is no previous window or it cost nothing.
    total_cost_delta_pct: float | None
    distance_km: float | None
    cost_per_km: float | None
    avg_consumption_l_per_100km: float | None
    # Absolute l/100 km, not percent.
    avg_consumption_delta: float | None
    # Fuel cost over litres bought in the window, in Kč/l; delta is absolute.
    avg_price_per_liter: float | None
    avg_price_per_liter_delta: float | None
    consumption_interval_count: int
    cost_breakdown: CostBreakdown
    fuel_trend: list[FuelTrendPoint]
    monthly_costs: list[MonthlyCostPoint]
    monthly_granularity: Literal["month", "year"]
    upcoming_reminders: list[ReminderRead]
    recent_activity: list[TimelineItem]

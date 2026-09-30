from collections.abc import Sequence
from datetime import date
from typing import Literal

from sqlmodel import Session, select

from app.car.models import CarProfileRead
from app.car.service import get_or_create_profile
from app.dashboard.periods import DateWindow, parse_period, previous_window
from app.dashboard.schemas import (
    CostBreakdown,
    CostTotals,
    Dashboard,
    FuelTimelineItem,
    FuelTrendPoint,
    MonthlyCostPoint,
    PeriodInfo,
    ServiceTimelineItem,
    TimelineItem,
)
from app.fuel.models import FuelEntry
from app.fuel.service import FullToFullInterval, full_to_full_intervals, list_entries_with_stats
from app.maintenance.models import ServiceEntry
from app.reminders.service import list_active_reminders

RECENT_ACTIVITY_LIMIT = 10
# Past this many months, monthly_costs switches to yearly buckets so a long
# history doesn't hand a phone screen a hundred columns.
MAX_MONTHLY_BUCKETS = 36


def _fuel_cost_czk(entry: FuelEntry) -> float:
    return entry.liters * entry.price_per_liter * entry.exchange_rate


def _service_cost_czk(entry: ServiceEntry) -> float:
    return entry.cost * entry.exchange_rate


def _avg_consumption(intervals: Sequence[FullToFullInterval]) -> float | None:
    """Litres burned per 100 km over the given full-to-full intervals.

    Totals first, divide once — so a short top-up can't pull the figure around
    as much as a long tank. Averaging each interval's own
    `consumption_l_per_100km` would weight them equally instead.
    """
    total_km = sum(i.distance_km for i in intervals)
    if total_km <= 0:
        return None
    return round(sum(i.liters for i in intervals) / total_km * 100, 2)


def _totals(fuel: Sequence[FuelEntry], service: Sequence[ServiceEntry]) -> CostTotals:
    fuel_cost = sum(_fuel_cost_czk(e) for e in fuel)
    service_cost = sum(_service_cost_czk(e) for e in service)
    return CostTotals(
        fuel=round(fuel_cost, 2),
        fuel_liters=round(sum(e.liters for e in fuel), 2),
        fuel_entries=len(fuel),
        maintenance=round(service_cost, 2),
        maintenance_entries=len(service),
        total=round(fuel_cost + service_cost, 2),
    )


def _distance_km(
    window: DateWindow,
    today: date,
    current_mileage_km: float,
    fuel: Sequence[FuelEntry],
    service: Sequence[ServiceEntry],
) -> float | None:
    """Km driven over the window.

    Starts from the newest reading *before* the window, so the stretch driven
    between it and the first in-window entry counts too, falling back to the
    lowest in-window reading when there is nothing earlier. Ends at the
    odometer when the window reaches today, else at the newest reading inside
    it. For `all` this is current mileage minus the lowest reading ever.
    """
    readings = sorted(
        [(e.date, e.mileage_km) for e in fuel] + [(e.date, e.mileage_km) for e in service]
    )
    in_window = [km for d, km in readings if window.contains(d)]
    if not in_window:
        return None
    before = [km for d, km in readings if window.start is not None and d < window.start]
    start_km = before[-1] if before else min(in_window)
    if window.end is None or window.end >= today:
        end_km = current_mileage_km
    else:
        end_km = max(km for d, km in readings if d <= window.end)
    return end_km - start_km


def _bucket_bounds(
    window: DateWindow, today: date, fuel: Sequence[FuelEntry], service: Sequence[ServiceEntry]
) -> tuple[date, date] | None:
    dates = [e.date for e in fuel] + [e.date for e in service]
    start = window.start if window.start is not None else min(dates, default=None)
    end = window.end if window.end is not None else max([today, *dates])
    if start is None:
        return None
    return start, end


def _monthly_costs(
    bounds: tuple[date, date] | None,
    fuel: Sequence[FuelEntry],
    service: Sequence[ServiceEntry],
) -> tuple[list[MonthlyCostPoint], Literal["month", "year"]]:
    """Costs per month (or per year over long windows), with every bucket in
    the window present — a month with no spending is a zero, not a gap in the
    axis.
    """
    if bounds is None:
        return [], "month"
    start, end = bounds
    months = (end.year - start.year) * 12 + end.month - start.month + 1
    granularity: Literal["month", "year"] = "year" if months > MAX_MONTHLY_BUCKETS else "month"

    def key(d: date) -> str:
        return str(d.year) if granularity == "year" else f"{d.year}-{d.month:02d}"

    if granularity == "year":
        keys = [str(y) for y in range(start.year, end.year + 1)]
    else:
        index = start.year * 12 + start.month - 1
        keys = [f"{i // 12}-{i % 12 + 1:02d}" for i in range(index, index + months)]

    buckets = {k: [0.0, 0.0] for k in keys}
    for e in fuel:
        buckets[key(e.date)][0] += _fuel_cost_czk(e)
    for e in service:
        buckets[key(e.date)][1] += _service_cost_czk(e)
    points = [
        MonthlyCostPoint(bucket=k, fuel=round(f, 2), service=round(s, 2))
        for k, (f, s) in buckets.items()
    ]
    return points, granularity


def _cost_breakdown(fuel: Sequence[FuelEntry], service: Sequence[ServiceEntry]) -> CostBreakdown:
    by_type: dict[str, float] = {}
    for e in service:
        by_type[e.type.value] = round(by_type.get(e.type.value, 0) + _service_cost_czk(e), 2)
    return CostBreakdown(
        fuel_total=round(sum(_fuel_cost_czk(e) for e in fuel), 2), maintenance_by_type=by_type
    )


def _timeline(fuel: Sequence[FuelEntry], service: Sequence[ServiceEntry]) -> list[TimelineItem]:
    timeline: list[TimelineItem] = [
        FuelTimelineItem(date=e.date, cost=round(_fuel_cost_czk(e), 2), liters=e.liters)
        for e in fuel
    ]
    timeline += [
        ServiceTimelineItem(
            date=e.date,
            cost=round(_service_cost_czk(e), 2),
            service_type=e.type,
            description=e.description,
        )
        for e in service
    ]
    timeline.sort(key=lambda item: item.date, reverse=True)
    return timeline[:RECENT_ACTIVITY_LIMIT]


def get_dashboard(db: Session, period: str, today: date | None = None) -> Dashboard:
    today = today or date.today()
    window = parse_period(period, today)
    previous = previous_window(period, today)
    profile = get_or_create_profile(db)

    all_fuel = db.exec(select(FuelEntry)).all()
    all_service = db.exec(select(ServiceEntry)).all()

    # Costs filter *entries*: a cost happens on a date. Consumption below
    # filters *intervals* instead — see the Dashboard docstring for why.
    fuel = [e for e in all_fuel if window.contains(e.date)]
    service = [e for e in all_service if window.contains(e.date)]
    totals = _totals(fuel, service)

    intervals = full_to_full_intervals(all_fuel)
    in_window = [i for i in intervals if window.contains(i.date)]
    avg_consumption = _avg_consumption(in_window)

    previous_totals = None
    total_cost_delta_pct = None
    avg_consumption_delta = None
    if previous is not None:
        previous_totals = _totals(
            [e for e in all_fuel if previous.contains(e.date)],
            [e for e in all_service if previous.contains(e.date)],
        )
        if previous_totals.total > 0:
            total_cost_delta_pct = round(
                (totals.total - previous_totals.total) / previous_totals.total * 100, 1
            )
        previous_consumption = _avg_consumption([i for i in intervals if previous.contains(i.date)])
        if avg_consumption is not None and previous_consumption is not None:
            avg_consumption_delta = round(avg_consumption - previous_consumption, 2)

    distance_km = _distance_km(window, today, profile.current_mileage_km, all_fuel, all_service)
    cost_per_km = None
    if distance_km is not None and distance_km > 0:
        cost_per_km = round(totals.total / distance_km, 2)

    monthly_costs, granularity = _monthly_costs(
        _bucket_bounds(window, today, all_fuel, all_service), fuel, service
    )

    fuel_trend = [
        FuelTrendPoint(
            date=e.date,
            price_total=e.price_total_czk,
            liters=e.liters,
            price_per_liter=e.price_per_liter_czk,
            consumption_l_per_100km=e.consumption_l_per_100km,
        )
        for e in sorted(list_entries_with_stats(db), key=lambda e: e.date)
        if window.contains(e.date)
    ]

    years = {e.date.year for e in all_fuel} | {e.date.year for e in all_service}

    return Dashboard(
        period=PeriodInfo(
            key=period,
            start=window.start,
            end=window.end,
            previous_start=previous.start if previous else None,
            previous_end=previous.end if previous else None,
        ),
        available_years=sorted(years, reverse=True),
        car=CarProfileRead.model_validate(profile, from_attributes=True),
        totals=totals,
        previous_totals=previous_totals,
        total_cost_delta_pct=total_cost_delta_pct,
        distance_km=distance_km,
        cost_per_km=cost_per_km,
        avg_consumption_l_per_100km=avg_consumption,
        avg_consumption_delta=avg_consumption_delta,
        consumption_interval_count=len(in_window),
        cost_breakdown=_cost_breakdown(fuel, service),
        fuel_trend=fuel_trend,
        monthly_costs=monthly_costs,
        monthly_granularity=granularity,
        upcoming_reminders=list_active_reminders(db),
        recent_activity=_timeline(fuel, service),
    )

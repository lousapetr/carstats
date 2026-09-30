from collections.abc import Sequence
from datetime import date

from sqlmodel import Session, select

from app.car.models import CarProfileRead
from app.car.service import get_or_create_profile
from app.dashboard.schemas import (
    CostBreakdown,
    DashboardSummary,
    FuelTimelineItem,
    FuelTrendPoint,
    ServiceTimelineItem,
    TimelineItem,
)
from app.fuel.models import FuelEntry
from app.fuel.service import FullToFullInterval, full_to_full_intervals, list_entries_with_stats
from app.maintenance.models import ServiceEntry
from app.reminders.service import list_active_reminders

RECENT_ACTIVITY_LIMIT = 10


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


def get_summary(db: Session) -> DashboardSummary:
    this_year = date.today().year
    profile = get_or_create_profile(db)
    fuel_entries = db.exec(select(FuelEntry)).all()
    fuel_entries_this_year = [e for e in fuel_entries if e.date.year == this_year]
    fuel_entries_last_year = [e for e in fuel_entries if e.date.year == this_year - 1]
    service_entries = db.exec(select(ServiceEntry)).all()
    service_entries_this_year = [e for e in service_entries if e.date.year == this_year]
    service_entries_last_year = [e for e in service_entries if e.date.year == this_year - 1]

    total_fuel_cost = sum(_fuel_cost_czk(e) for e in fuel_entries)
    total_fuel_liters = sum(e.liters for e in fuel_entries)
    total_maintenance_cost = sum(_service_cost_czk(e) for e in service_entries)

    total_cost_this_year = sum(_fuel_cost_czk(e) for e in fuel_entries_this_year) + sum(
        _service_cost_czk(e) for e in service_entries_this_year
    )
    total_cost_last_year = sum(_fuel_cost_czk(e) for e in fuel_entries_last_year) + sum(
        _service_cost_czk(e) for e in service_entries_last_year
    )

    all_mileages = [e.mileage_km for e in fuel_entries] + [e.mileage_km for e in service_entries]
    cost_per_km = None
    if all_mileages:
        distance_driven = profile.current_mileage_km - min(all_mileages)
        if distance_driven > 0:
            cost_per_km = round((total_fuel_cost + total_maintenance_cost) / distance_driven, 2)

    # Intervals are derived from the whole history, then bucketed by the year of
    # the full tank that closes each one — an interval spanning New Year counts
    # under the year it ended in, matching where its consumption figure shows up
    # in the fuel list.
    intervals = full_to_full_intervals(fuel_entries)
    avg_consumption = _avg_consumption(intervals)
    avg_consumption_this_year = _avg_consumption([i for i in intervals if i.date.year == this_year])
    avg_consumption_last_year = _avg_consumption(
        [i for i in intervals if i.date.year == this_year - 1]
    )

    # Newest first by odometer rather than date, which can't order two
    # entries logged on the same day.
    by_mileage: list[tuple[float, TimelineItem]] = [
        (
            e.mileage_km,
            FuelTimelineItem(date=e.date, cost=round(_fuel_cost_czk(e), 2), liters=e.liters),
        )
        for e in fuel_entries
    ]
    by_mileage += [
        (
            e.mileage_km,
            ServiceTimelineItem(
                date=e.date,
                cost=round(_service_cost_czk(e), 2),
                service_type=e.type,
                description=e.description,
            ),
        )
        for e in service_entries
    ]
    by_mileage.sort(key=lambda pair: pair[0], reverse=True)
    timeline = [item for _, item in by_mileage]

    return DashboardSummary(
        car=CarProfileRead.model_validate(profile, from_attributes=True),
        total_fuel_cost=round(total_fuel_cost, 2),
        total_fuel_liters=round(total_fuel_liters, 2),
        total_fuel_entries=len(fuel_entries),
        total_maintenance_cost=round(total_maintenance_cost, 2),
        total_maintenance_entries=len(service_entries),
        total_cost=round(total_fuel_cost + total_maintenance_cost, 2),
        total_cost_this_year=round(total_cost_this_year, 2),
        total_cost_last_year=round(total_cost_last_year, 2),
        cost_per_km=cost_per_km,
        avg_consumption_l_per_100km=avg_consumption,
        avg_consumption_l_per_100km_this_year=avg_consumption_this_year,
        avg_consumption_l_per_100km_last_year=avg_consumption_last_year,
        upcoming_reminders=list_active_reminders(db),
        recent_activity=timeline[:RECENT_ACTIVITY_LIMIT],
    )


def get_fuel_trend(db: Session) -> list[FuelTrendPoint]:
    # Oldest first by odometer, not date, so same-day fill-ups stay in order.
    entries = list(reversed(list_entries_with_stats(db)))
    return [
        FuelTrendPoint(
            date=e.date,
            price_total=e.price_total_czk,
            liters=e.liters,
            price_per_liter=e.price_per_liter_czk,
            consumption_l_per_100km=e.consumption_l_per_100km,
        )
        for e in entries
    ]


def get_cost_breakdown(db: Session) -> CostBreakdown:
    fuel_entries = db.exec(select(FuelEntry)).all()
    service_entries = db.exec(select(ServiceEntry)).all()

    total_fuel_cost = round(sum(_fuel_cost_czk(e) for e in fuel_entries), 2)

    by_type: dict[str, float] = {}
    for e in service_entries:
        by_type[e.type.value] = round(by_type.get(e.type.value, 0) + _service_cost_czk(e), 2)

    return CostBreakdown(fuel_total=total_fuel_cost, maintenance_by_type=by_type)

from sqlmodel import Session, select

from app.car.service import get_or_create_profile
from app.dashboard.schemas import CostBreakdown, DashboardSummary, FuelTrendPoint, TimelineItem
from app.fuel.models import FuelEntry
from app.fuel.service import list_entries_with_stats
from app.maintenance.models import ServiceEntry
from app.reminders.service import list_active_reminders

RECENT_ACTIVITY_LIMIT = 10


def get_summary(db: Session) -> DashboardSummary:
    profile = get_or_create_profile(db)
    fuel_entries = db.exec(select(FuelEntry)).all()
    service_entries = db.exec(select(ServiceEntry)).all()

    total_fuel_cost = sum(e.price_total for e in fuel_entries)
    total_fuel_liters = sum(e.liters for e in fuel_entries)
    total_maintenance_cost = sum(e.cost for e in service_entries)

    consumptions = [
        e.consumption_l_per_100km
        for e in list_entries_with_stats(db)
        if e.consumption_l_per_100km is not None
    ]
    avg_consumption = round(sum(consumptions) / len(consumptions), 2) if consumptions else None

    timeline = [
        TimelineItem(
            date=e.date, kind="fuel", label=f"Fuel fill-up ({e.liters:g} L)", cost=e.price_total
        )
        for e in fuel_entries
    ] + [
        TimelineItem(
            date=e.date, kind="service", label=e.type.replace("_", " ").title(), cost=e.cost
        )
        for e in service_entries
    ]
    timeline.sort(key=lambda item: item.date, reverse=True)

    return DashboardSummary(
        car={
            "make": profile.make,
            "model": profile.model,
            "year": profile.year,
            "current_mileage_km": profile.current_mileage_km,
        },
        total_fuel_cost=round(total_fuel_cost, 2),
        total_fuel_liters=round(total_fuel_liters, 2),
        total_fuel_entries=len(fuel_entries),
        total_maintenance_cost=round(total_maintenance_cost, 2),
        total_maintenance_entries=len(service_entries),
        total_cost=round(total_fuel_cost + total_maintenance_cost, 2),
        avg_consumption_l_per_100km=avg_consumption,
        upcoming_reminders=list_active_reminders(db),
        recent_activity=timeline[:RECENT_ACTIVITY_LIMIT],
    )


def get_fuel_trend(db: Session) -> list[FuelTrendPoint]:
    entries = sorted(list_entries_with_stats(db), key=lambda e: e.date)
    return [
        FuelTrendPoint(
            date=e.date,
            price_total=e.price_total,
            liters=e.liters,
            price_per_liter=e.price_per_liter,
            consumption_l_per_100km=e.consumption_l_per_100km,
        )
        for e in entries
    ]


def get_cost_breakdown(db: Session) -> CostBreakdown:
    fuel_entries = db.exec(select(FuelEntry)).all()
    service_entries = db.exec(select(ServiceEntry)).all()

    total_fuel_cost = round(sum(e.price_total for e in fuel_entries), 2)

    by_type: dict[str, float] = {}
    for e in service_entries:
        by_type[e.type.value] = round(by_type.get(e.type.value, 0) + e.cost, 2)

    return CostBreakdown(fuel_total=total_fuel_cost, maintenance_by_type=by_type)

from datetime import date

from sqlmodel import Session, select

from app.car.service import get_or_create_profile
from app.dashboard.schemas import CostBreakdown, DashboardSummary, FuelTrendPoint, TimelineItem
from app.fuel.models import FuelEntry
from app.fuel.service import list_entries_with_stats
from app.maintenance.models import ServiceEntry, ServiceType
from app.reminders.service import list_active_reminders

RECENT_ACTIVITY_LIMIT = 10

SERVICE_TYPE_LABELS_CS = {
    "oil_change": "Výměna oleje",
    "tires": "Pneumatiky",
    "engine_service": "Servis motoru",
    "additives": "Aditiva",
    "other": "Jiné",
}


def _fuel_cost_czk(entry: FuelEntry) -> float:
    return entry.liters * entry.price_per_liter * entry.exchange_rate


def _service_cost_czk(entry: ServiceEntry) -> float:
    return entry.cost * entry.exchange_rate


def _service_label(entry: ServiceEntry) -> str:
    label = SERVICE_TYPE_LABELS_CS.get(entry.type.value, entry.type.value)
    if entry.type == ServiceType.other and entry.description:
        return f"{label} - {entry.description}"
    return label


def get_summary(db: Session) -> DashboardSummary:
    profile = get_or_create_profile(db)
    fuel_entries = db.exec(select(FuelEntry)).all()
    service_entries = db.exec(select(ServiceEntry)).all()

    total_fuel_cost = sum(_fuel_cost_czk(e) for e in fuel_entries)
    total_fuel_liters = sum(e.liters for e in fuel_entries)
    total_maintenance_cost = sum(_service_cost_czk(e) for e in service_entries)

    this_year = date.today().year
    total_cost_this_year = sum(
        _fuel_cost_czk(e) for e in fuel_entries if e.date.year == this_year
    ) + sum(_service_cost_czk(e) for e in service_entries if e.date.year == this_year)
    total_cost_last_year = sum(
        _fuel_cost_czk(e) for e in fuel_entries if e.date.year == this_year - 1
    ) + sum(_service_cost_czk(e) for e in service_entries if e.date.year == this_year - 1)

    all_mileages = [e.mileage_km for e in fuel_entries] + [e.mileage_km for e in service_entries]
    cost_per_km = None
    if all_mileages:
        distance_driven = profile.current_mileage_km - min(all_mileages)
        if distance_driven > 0:
            cost_per_km = round(
                (total_fuel_cost + total_maintenance_cost) / distance_driven, 2
            )

    consumptions = [
        e.consumption_l_per_100km
        for e in list_entries_with_stats(db)
        if e.consumption_l_per_100km is not None
    ]
    avg_consumption = round(sum(consumptions) / len(consumptions), 2) if consumptions else None

    timeline = [
        TimelineItem(
            date=e.date,
            kind="fuel",
            label=f"Tankování ({e.liters:g} l)",
            cost=round(_fuel_cost_czk(e), 2),
        )
        for e in fuel_entries
    ] + [
        TimelineItem(
            date=e.date,
            kind="service",
            label=_service_label(e),
            cost=round(_service_cost_czk(e), 2),
        )
        for e in service_entries
    ]
    timeline.sort(key=lambda item: item.date, reverse=True)

    return DashboardSummary(
        car={
            "name": profile.name,
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
        total_cost_this_year=round(total_cost_this_year, 2),
        total_cost_last_year=round(total_cost_last_year, 2),
        cost_per_km=cost_per_km,
        avg_consumption_l_per_100km=avg_consumption,
        upcoming_reminders=list_active_reminders(db),
        recent_activity=timeline[:RECENT_ACTIVITY_LIMIT],
    )


def get_fuel_trend(db: Session) -> list[FuelTrendPoint]:
    entries = sorted(list_entries_with_stats(db), key=lambda e: e.date)
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

import csv
import io

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlmodel import col, select

from app.core.database import DbSession
from app.core.security import CurrentUser
from app.fuel.models import FuelEntry
from app.maintenance.models import ServiceEntry

router = APIRouter(prefix="/export", tags=["export"])


def _csv_response(rows: list[list[str]], header: list[str], filename: str) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _fuel_row(e: FuelEntry) -> list[str]:
    # Only complete entries are exported; a missing field is a bug, not a row to skip.
    assert e.date is not None and e.mileage_km is not None
    assert e.liters is not None and e.price_per_liter is not None
    total = e.liters * e.price_per_liter
    return [
        str(e.date),
        f"{e.mileage_km:g}",
        f"{e.liters:g}",
        f"{e.price_per_liter:.2f}",
        e.currency.value,
        f"{total:.2f}",
        f"{total * e.exchange_rate:.2f}",
        e.notes or "",
    ]


def _service_row(e: ServiceEntry) -> list[str]:
    assert e.date is not None and e.mileage_km is not None and e.cost is not None
    return [
        str(e.date),
        f"{e.mileage_km:g}",
        e.type.value,
        e.description or "",
        f"{e.cost:.2f}",
        e.currency.value,
        f"{e.cost * e.exchange_rate:.2f}",
        e.notes or "",
    ]


@router.get("/fuel.csv")
def export_fuel_csv(user: CurrentUser, db: DbSession) -> StreamingResponse:
    entries = db.exec(
        select(FuelEntry)
        .where(col(FuelEntry.is_draft).is_(False))
        .order_by(col(FuelEntry.mileage_km), col(FuelEntry.id))
    ).all()
    rows = [_fuel_row(e) for e in entries]
    header = [
        "Datum",
        "Najeto (km)",
        "Litry",
        "Cena/l",
        "Měna",
        "Celkem (měna)",
        "Celkem (Kč)",
        "Poznámka",
    ]
    return _csv_response(rows, header, "tankovani.csv")


@router.get("/maintenance.csv")
def export_maintenance_csv(user: CurrentUser, db: DbSession) -> StreamingResponse:
    entries = db.exec(
        select(ServiceEntry)
        .where(col(ServiceEntry.is_draft).is_(False))
        .order_by(col(ServiceEntry.mileage_km), col(ServiceEntry.id))
    ).all()
    rows = [_service_row(e) for e in entries]
    header = ["Datum", "Najeto (km)", "Typ", "Popis", "Cena", "Měna", "Cena (Kč)", "Poznámka"]
    return _csv_response(rows, header, "servis.csv")

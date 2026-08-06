import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.core.database import get_db
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


@router.get("/fuel.csv")
def export_fuel_csv(user: CurrentUser, db: Session = Depends(get_db)) -> StreamingResponse:
    entries = db.exec(select(FuelEntry).order_by(FuelEntry.date)).all()
    rows = [
        [
            str(e.date),
            f"{e.mileage_km:g}",
            f"{e.liters:g}",
            f"{e.price_per_liter:.2f}",
            e.currency.value,
            f"{e.liters * e.price_per_liter:.2f}",
            f"{e.liters * e.price_per_liter * e.exchange_rate:.2f}",
            e.notes or "",
        ]
        for e in entries
    ]
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
def export_maintenance_csv(user: CurrentUser, db: Session = Depends(get_db)) -> StreamingResponse:
    entries = db.exec(select(ServiceEntry).order_by(ServiceEntry.date)).all()
    rows = [
        [
            str(e.date),
            f"{e.mileage_km:g}",
            e.type.value,
            e.description or "",
            f"{e.cost:.2f}",
            e.currency.value,
            f"{e.cost * e.exchange_rate:.2f}",
            e.notes or "",
        ]
        for e in entries
    ]
    header = ["Datum", "Najeto (km)", "Typ", "Popis", "Cena", "Měna", "Cena (Kč)", "Poznámka"]
    return _csv_response(rows, header, "servis.csv")

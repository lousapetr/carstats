from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_db
from app.core.security import CurrentUser
from app.currency import service
from app.currency.models import Currency
from app.currency.schemas import CurrencyRateRead, CurrencyRateUpdate

router = APIRouter(prefix="/currency-rates", tags=["currency"])


@router.get("", response_model=list[CurrencyRateRead])
def list_currency_rates(user: CurrentUser, db: Session = Depends(get_db)) -> list[CurrencyRateRead]:
    return service.list_rates(db)


@router.put("/{currency}", response_model=CurrencyRateRead)
def update_currency_rate(
    currency: Currency, data: CurrencyRateUpdate, user: CurrentUser, db: Session = Depends(get_db)
) -> CurrencyRateRead:
    try:
        return service.update_rate(db, currency, data.rate_to_czk)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

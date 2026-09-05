from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_db
from app.core.security import CurrentUser
from app.currency import service
from app.currency.schemas import CurrencyRateRead

router = APIRouter(prefix="/currency-rates", tags=["currency"])


@router.get("", response_model=list[CurrencyRateRead])
def list_currency_rates(user: CurrentUser, db: Session = Depends(get_db)) -> list[CurrencyRateRead]:
    return service.list_rates(db)

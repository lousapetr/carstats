from fastapi import APIRouter

from app.core.database import DbSession
from app.core.security import CurrentUser
from app.currency import service
from app.currency.models import CurrencyRate, CurrencyRateRead

router = APIRouter(prefix="/currency-rates", tags=["currency"])


@router.get("", response_model=list[CurrencyRateRead])
def list_currency_rates(user: CurrentUser, db: DbSession) -> list[CurrencyRate]:
    return service.list_rates(db)

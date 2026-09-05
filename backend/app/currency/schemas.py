from pydantic import BaseModel

from app.currency.models import Currency


class CurrencyRateRead(BaseModel):
    currency: Currency
    rate_to_czk: float

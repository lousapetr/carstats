from datetime import UTC, datetime

from sqlmodel import Session, select

from app.currency.models import DEFAULT_RATES_TO_CZK, Currency, CurrencyRate


def _get_or_seed_row(db: Session, currency: Currency) -> CurrencyRate:
    row = db.exec(select(CurrencyRate).where(CurrencyRate.currency == currency)).first()
    if row is None:
        row = CurrencyRate(currency=currency, rate_to_czk=DEFAULT_RATES_TO_CZK[currency])
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def list_rates(db: Session) -> list[CurrencyRate]:
    for currency in DEFAULT_RATES_TO_CZK:
        _get_or_seed_row(db, currency)
    return db.exec(select(CurrencyRate).order_by(CurrencyRate.currency)).all()


def get_rate(db: Session, currency: Currency) -> float:
    if currency == Currency.CZK:
        return 1.0
    return _get_or_seed_row(db, currency).rate_to_czk


def update_rate(db: Session, currency: Currency, rate_to_czk: float) -> CurrencyRate:
    if currency == Currency.CZK:
        raise ValueError("Kurz CZK je pevně 1,0 a nelze jej změnit")
    row = _get_or_seed_row(db, currency)
    row.rate_to_czk = rate_to_czk
    row.updated_at = datetime.now(UTC)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

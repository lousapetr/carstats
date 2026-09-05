from datetime import UTC, datetime

from sqlmodel import Session, select

from app.currency import cnb_client
from app.currency.models import DEFAULT_RATES_TO_CZK, Currency, CurrencyRate


def _get_or_seed_row(db: Session, currency: Currency) -> CurrencyRate:
    row = db.exec(select(CurrencyRate).where(CurrencyRate.currency == currency)).first()
    if row is None:
        row = CurrencyRate(currency=currency, rate_to_czk=DEFAULT_RATES_TO_CZK[currency])
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def update_rate(db: Session, currency: Currency, rate_to_czk: float) -> CurrencyRate:
    row = _get_or_seed_row(db, currency)
    row.rate_to_czk = rate_to_czk
    row.updated_at = datetime.now(UTC)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _ensure_rates_fresh(db: Session) -> None:
    """Fetch the ČNB daily fixing at most once per calendar day, so a whole
    day's worth of fuel/service entries in different currencies share one
    cached fetch instead of hitting the network per entry (or on a fixed
    schedule regardless of whether the app is even used that day).
    """
    latest = db.exec(select(CurrencyRate).order_by(CurrencyRate.updated_at.desc())).first()
    if latest is not None and latest.updated_at.date() >= datetime.now(UTC).date():
        return
    try:
        rates = cnb_client.parse_rates(cnb_client.fetch_daily_text())
    except Exception:
        return  # keep whatever we have (seeded defaults or a previous day's cache)
    for currency, rate in rates.items():
        if currency in DEFAULT_RATES_TO_CZK:
            update_rate(db, currency, rate)


def list_rates(db: Session) -> list[CurrencyRate]:
    _ensure_rates_fresh(db)
    for currency in DEFAULT_RATES_TO_CZK:
        _get_or_seed_row(db, currency)
    return db.exec(select(CurrencyRate).order_by(CurrencyRate.currency)).all()


def get_rate(db: Session, currency: Currency) -> float:
    if currency == Currency.CZK:
        return 1.0
    _ensure_rates_fresh(db)
    return _get_or_seed_row(db, currency).rate_to_czk

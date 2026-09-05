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


def resolve_exchange_rate(db: Session, currency: Currency, override: float | None) -> float:
    """The rate to snapshot on a fuel/service entry: `override` (from an
    entry form editing the rate inline) updates the Settings default and is
    used as-is, otherwise falls back to today's default via `get_rate`.
    CZK is never overridable — its rate is always 1.0.
    """
    if currency == Currency.CZK or override is None:
        return get_rate(db, currency)
    if override != get_rate(db, currency):
        update_rate(db, currency, override)
    return override


def refresh_all_rates(db: Session) -> dict[Currency, float]:
    """Fetch the latest ČNB daily fixing and overwrite every currency's
    Settings default with it. Run once a day (see refresh_rates.sh) — this
    intentionally overwrites any manual edit made via Settings or an entry
    form's rate override, since those are meant as same-day corrections.
    """
    rates = cnb_client.parse_rates(cnb_client.fetch_daily_text())
    for currency, rate in rates.items():
        if currency in DEFAULT_RATES_TO_CZK:
            update_rate(db, currency, rate)
    return rates

#!/usr/bin/env python
"""Refresh currency exchange rates from the ČNB daily fixing.

Run manually from backend/ (`python -m scripts.refresh_exchange_rates`) or
via cron/refresh_rates.sh — see README.md.
"""

import sys

from sqlmodel import Session

from app.core.database import engine
from app.currency.service import refresh_all_rates


def main() -> int:
    with Session(engine) as db:
        try:
            rates = refresh_all_rates(db)
        except Exception as exc:
            print(f"Failed to refresh exchange rates: {exc}", file=sys.stderr)
            return 1

    for currency, rate in sorted(rates.items()):
        print(f"{currency.value}: {rate:g}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

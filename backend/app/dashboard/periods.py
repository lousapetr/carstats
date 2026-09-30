"""The dashboard's `period` parameter: `all`, `ytd`, `12m` or `year:YYYY`.

Relative periods are resolved against a `today` passed in by the caller, so a
single request computes every window from the same date.
"""

import calendar
from dataclasses import dataclass
from datetime import date, timedelta

PERIOD_PATTERN = r"^(all|ytd|12m|year:[1-9]\d{3})$"


@dataclass(frozen=True)
class DateWindow:
    """Inclusive on both ends; None means unbounded on that side."""

    start: date | None
    end: date | None

    def contains(self, d: date) -> bool:
        return (self.start is None or d >= self.start) and (self.end is None or d <= self.end)


def _month_start(d: date, months_back: int) -> date:
    index = d.year * 12 + (d.month - 1) - months_back
    return date(index // 12, index % 12 + 1, 1)


def _same_day_in_year(d: date, year: int) -> date:
    # 29 Feb has no counterpart in a non-leap year; fall back to the 28th.
    return date(year, d.month, min(d.day, calendar.monthrange(year, d.month)[1]))


def _year(period: str) -> int:
    return int(period.removeprefix("year:"))


def parse_period(period: str, today: date) -> DateWindow:
    if period == "all":
        return DateWindow(None, None)
    if period == "ytd":
        return DateWindow(date(today.year, 1, 1), today)
    if period == "12m":
        # Twelve whole month buckets: the current month plus the eleven before it.
        return DateWindow(_month_start(today, 11), today)
    if period.startswith("year:"):
        year = _year(period)
        return DateWindow(date(year, 1, 1), date(year, 12, 31))
    raise ValueError(f"Unknown period: {period}")


def previous_window(period: str, today: date) -> DateWindow | None:
    """The window a period is compared against, or None for `all`.

    `ytd` compares against the *same stretch* of last year, not all of it —
    Jan–Sep against a full year would report a fake saving every autumn.
    """
    if period == "all":
        return None
    if period == "ytd":
        return DateWindow(date(today.year - 1, 1, 1), _same_day_in_year(today, today.year - 1))
    if period == "12m":
        return DateWindow(_month_start(today, 23), _month_start(today, 11) - timedelta(days=1))
    if period.startswith("year:"):
        year = _year(period) - 1
        return DateWindow(date(year, 1, 1), date(year, 12, 31))
    raise ValueError(f"Unknown period: {period}")

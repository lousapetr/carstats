from datetime import date


class DuplicateEntryError(Exception):
    """Entry matches an existing one; routers map it to 409, `?force=true` bypasses.

    Deliberately not a ValueError: routers map that to 400, and the client needs
    a distinct status to offer "save anyway".
    """


def normalize_text(value: str | None) -> str:
    return " ".join((value or "").split()).casefold()


def czech_date(d: date) -> str:
    return f"{d.day}. {d.month}. {d.year}"

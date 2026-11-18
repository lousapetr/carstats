from pydantic_core import PydanticCustomError


def draft_empty_error() -> PydanticCustomError:
    return PydanticCustomError(
        "draft_empty", "Rozpracovaný záznam musí obsahovat aspoň jeden údaj."
    )


def missing_fields_error(labels: list[str]) -> PydanticCustomError:
    return PydanticCustomError(
        "missing_fields", "Chybí povinné údaje: {fields}.", {"fields": ", ".join(labels)}
    )


def has_content(*values: object) -> bool:
    """True when any value is set; text counts only if non-blank after trimming."""
    return any(v.strip() != "" if isinstance(v, str) else v is not None for v in values)

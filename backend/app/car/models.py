from sqlmodel import Field, SQLModel


class CarProfile(SQLModel, table=True):
    """Single-row table describing the one car this app tracks."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = ""
    make: str = ""
    model: str = ""
    year: int | None = None
    current_mileage_km: float = 0

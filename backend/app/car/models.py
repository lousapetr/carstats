from sqlmodel import Field, SQLModel


class CarProfileBase(SQLModel):
    name: str = ""
    make: str
    model: str
    year: int | None = None


class CarProfile(CarProfileBase, table=True):
    """Single-row table describing the one car this app tracks."""

    id: int | None = Field(default=None, primary_key=True)
    make: str = ""
    model: str = ""
    current_mileage_km: float = 0


class CarProfileUpdate(CarProfileBase):
    # Bounded so a typo'd year can't end up in the dashboard heading.
    year: int | None = Field(default=None, ge=1900, le=2100)


class CarProfileRead(CarProfileBase):
    current_mileage_km: float

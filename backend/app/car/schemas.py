from pydantic import BaseModel


class CarProfileRead(BaseModel):
    make: str
    model: str
    year: int | None
    current_mileage_km: float


class CarProfileUpdate(BaseModel):
    make: str
    model: str
    year: int | None = None

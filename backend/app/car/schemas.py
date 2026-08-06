from pydantic import BaseModel


class CarProfileRead(BaseModel):
    name: str
    make: str
    model: str
    year: int | None
    current_mileage_km: float


class CarProfileUpdate(BaseModel):
    name: str = ""
    make: str
    model: str
    year: int | None = None

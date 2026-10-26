"""Validated request and response shapes used by the HTTP API."""

from datetime import date
from pydantic import BaseModel, Field, validator


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=72)

    @validator("password")
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes")
        return value


class UserLogin(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=72)


class UserPublic(BaseModel):
    id: str
    name: str
    email: str


class AuthResponse(BaseModel):
    token: str
    user: UserPublic


class TripCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=160)
    start_date: date
    end_date: date


class Trip(TripCreate):
    id: str


class BudgetCalculate(BaseModel):
    destination: str = Field(min_length=1, max_length=160)
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    total_budget: float = Field(alias="totalBudget", gt=0)
    group_size: int = Field(default=1, alias="groupSize", ge=1, le=50)
    currency: str = Field(default="USD", min_length=3, max_length=3)

class BudgetPlan(BaseModel):
    id: str
    trip_id: str
    total_budget: float
    currency: str
    breakdown: dict[str, float]

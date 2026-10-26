"""VoyageIQ's local FastAPI backend."""

import json
import os
import sqlite3
from datetime import date
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.requests import Request

load_dotenv()

from app.database import get_connection, initialize_database
from app.schemas import (
    AuthResponse,
    BudgetCalculate,
    BudgetPlan,
    Trip,
    TripCreate,
    UserCreate,
    UserLogin,
    UserPublic,
)
from app.security import create_access_token, hash_password, read_access_token, verify_password
from app.services.duffel import FlightProviderError, duffel_client


app = FastAPI(title="VoyageIQ Backend", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

initialize_database()
bearer_scheme = HTTPBearer(auto_error=False)


@app.exception_handler(HTTPException)
async def api_error_handler(request: Request, exc: HTTPException):
    """Keep API errors in the shape documented in API.md."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Request validation failed",
            "details": [
                {
                    "field": ".".join(str(part) for part in item["loc"] if part != "body"),
                    "message": item["msg"],
                }
                for item in exc.errors()
            ],
        },
    )


def validate_email(email: str) -> str:
    normalized = email.strip().lower()
    if normalized.count("@") != 1 or "." not in normalized.rsplit("@", 1)[-1]:
        raise HTTPException(status_code=400, detail="Enter a valid email address")
    return normalized


def require_valid_dates(start_date, end_date) -> None:
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="End date must be on or after start date")


def require_nonblank(value: str, label: str) -> None:
    if not value.strip():
        raise HTTPException(status_code=400, detail=f"{label} cannot be blank")


def public_user(row) -> UserPublic:
    return UserPublic(id=row["id"], name=row["name"], email=row["email"])


def trip_from_row(row) -> Trip:
    return Trip(
        id=row["id"],
        title=row["title"],
        destination=row["destination"],
        start_date=row["start_date"],
        end_date=row["end_date"],
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Sign in and send your access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = read_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Access token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with get_connection() as connection:
        user = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        raise HTTPException(status_code=401, detail="Account no longer exists")
    return user


def find_user_trip(trip_id: str, user_id: str):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM trips WHERE id = ? AND user_id = ?",
            (trip_id, user_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return row


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/flights/search")
async def search_flights(
    origin: str = Query(alias="from", min_length=3, max_length=3),
    destination: str = Query(alias="to", min_length=3, max_length=3),
    departure_date: date = Query(alias="date"),
    return_date: date | None = Query(default=None, alias="returnDate"),
    adults: int = Query(default=1, ge=1, le=9),
    children: int = Query(default=0, ge=0, le=9),
    non_stop: bool = Query(default=False, alias="nonStop"),
    currency_code: str = Query(default="USD", min_length=3, max_length=3, alias="currencyCode"),
    max_results: int = Query(default=20, ge=1, le=100, alias="max"),
):
    origin = origin.upper()
    destination = destination.upper()
    currency_code = currency_code.upper()
    if not origin.isalpha() or not destination.isalpha():
        raise HTTPException(status_code=400, detail="Use three-letter airport or city codes")
    if origin == destination:
        raise HTTPException(status_code=400, detail="Origin and destination must be different")
    if departure_date < date.today():
        raise HTTPException(status_code=400, detail="Departure date must be today or later")
    if return_date is not None and return_date <= departure_date:
        raise HTTPException(status_code=400, detail="Return date must be after departure date")
    if adults + children > 9:
        raise HTTPException(status_code=400, detail="The search supports up to nine seated travelers")
    if not currency_code.isalpha():
        raise HTTPException(status_code=400, detail="Currency must be a three-letter code")

    parameters = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date.isoformat(),
        "adults": adults,
        "children": children,
        "nonStop": str(non_stop).lower(),
        "currencyCode": currency_code,
        "max": max_results,
    }
    if return_date is not None:
        parameters["returnDate"] = return_date.isoformat()

    try:
        results = await duffel_client.search_flights(parameters)
    except FlightProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    return {
        "search": {
            "from": origin,
            "to": destination,
            "date": departure_date.isoformat(),
            "returnDate": return_date.isoformat() if return_date else None,
            "adults": adults,
            "children": children,
        },
        **results,
    }


@app.post("/api/auth/register", response_model=AuthResponse, status_code=201)
def register(user_data: UserCreate):
    email = validate_email(user_data.email)
    require_nonblank(user_data.name, "Name")
    user_id = str(uuid4())
    try:
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO users (id, name, email, password_hash) VALUES (?, ?, ?, ?)",
                (user_id, user_data.name.strip(), email, hash_password(user_data.password)),
            )
    except sqlite3.IntegrityError as exc:
        if "users.email" in str(exc):
            raise HTTPException(status_code=409, detail="An account with that email already exists")
        raise

    user = UserPublic(id=user_id, name=user_data.name.strip(), email=email)
    return AuthResponse(token=create_access_token(user_id), user=user)


@app.post("/api/auth/login", response_model=AuthResponse)
def login(credentials: UserLogin):
    email = validate_email(credentials.email)
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if row is None or not verify_password(credentials.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    return AuthResponse(token=create_access_token(row["id"]), user=public_user(row))


@app.get("/api/trips", response_model=list[Trip])
def list_trips(current_user=Depends(get_current_user)):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM trips WHERE user_id = ? ORDER BY created_at DESC, rowid DESC",
            (current_user["id"],),
        ).fetchall()
    return [trip_from_row(row) for row in rows]


@app.post("/api/trips", response_model=Trip, status_code=201)
def create_trip(trip_data: TripCreate, current_user=Depends(get_current_user)):
    require_valid_dates(trip_data.start_date, trip_data.end_date)
    require_nonblank(trip_data.title, "Title")
    require_nonblank(trip_data.destination, "Destination")
    trip_id = str(uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO trips (id, user_id, title, destination, start_date, end_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                trip_id,
                current_user["id"],
                trip_data.title.strip(),
                trip_data.destination.strip(),
                trip_data.start_date.isoformat(),
                trip_data.end_date.isoformat(),
            ),
        )
        row = connection.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
    return trip_from_row(row)


@app.get("/api/trips/{trip_id}", response_model=Trip)
def get_trip(trip_id: str, current_user=Depends(get_current_user)):
    return trip_from_row(find_user_trip(trip_id, current_user["id"]))


@app.put("/api/trips/{trip_id}", response_model=Trip)
def update_trip(trip_id: str, trip_data: TripCreate, current_user=Depends(get_current_user)):
    require_valid_dates(trip_data.start_date, trip_data.end_date)
    require_nonblank(trip_data.title, "Title")
    require_nonblank(trip_data.destination, "Destination")
    find_user_trip(trip_id, current_user["id"])
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE trips
            SET title = ?, destination = ?, start_date = ?, end_date = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                trip_data.title.strip(),
                trip_data.destination.strip(),
                trip_data.start_date.isoformat(),
                trip_data.end_date.isoformat(),
                trip_id,
                current_user["id"],
            ),
        )
        row = connection.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
    return trip_from_row(row)


@app.delete("/api/trips/{trip_id}", status_code=204)
def delete_trip(trip_id: str, current_user=Depends(get_current_user)):
    find_user_trip(trip_id, current_user["id"])
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM trips WHERE id = ? AND user_id = ?",
            (trip_id, current_user["id"]),
        )
    return Response(status_code=204)


def calculate_breakdown(total_budget: float) -> dict[str, float]:
    """Create a transparent starter allocation; it is not based on live prices."""
    allocations = [
        ("flights", 0.40),
        ("accommodation", 0.30),
        ("food", 0.15),
        ("activities", 0.10),
        ("local_transport", 0.05),
    ]
    breakdown = {}
    allocated = 0.0
    for category, share in allocations[:-1]:
        amount = round(total_budget * share, 2)
        breakdown[category] = amount
        allocated += amount
    breakdown[allocations[-1][0]] = round(total_budget - allocated, 2)
    return breakdown


@app.post("/api/budget/calculate")
def calculate_budget(request: BudgetCalculate):
    require_valid_dates(request.start_date, request.end_date)
    require_nonblank(request.destination, "Destination")
    breakdown = calculate_breakdown(request.total_budget)
    return {
        "destination": request.destination.strip(),
        "currency": request.currency.upper(),
        "totalBudget": round(request.total_budget, 2),
        "groupSize": request.group_size,
        "perPerson": round(request.total_budget / request.group_size, 2),
        "breakdown": breakdown,
        "estimateNote": "Starter planning estimate; amounts are not live travel prices.",
    }


@app.post("/api/trips/{trip_id}/budget", response_model=BudgetPlan, status_code=201)
def save_trip_budget(
    trip_id: str,
    request: BudgetCalculate,
    current_user=Depends(get_current_user),
):
    trip = find_user_trip(trip_id, current_user["id"])
    require_valid_dates(request.start_date, request.end_date)
    if request.destination.strip().casefold() != trip["destination"].strip().casefold():
        raise HTTPException(status_code=400, detail="Budget destination must match the trip")
    if (
        request.start_date.isoformat() != trip["start_date"]
        or request.end_date.isoformat() != trip["end_date"]
    ):
        raise HTTPException(status_code=400, detail="Budget dates must match the trip")

    breakdown = calculate_breakdown(request.total_budget)
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM budget_plans WHERE trip_id = ?", (trip_id,)
        ).fetchone()
        plan_id = existing["id"] if existing else str(uuid4())
        connection.execute(
            """
            INSERT INTO budget_plans (id, trip_id, total_budget, currency, breakdown)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(trip_id) DO UPDATE SET
                total_budget = excluded.total_budget,
                currency = excluded.currency,
                breakdown = excluded.breakdown,
                created_at = CURRENT_TIMESTAMP
            """,
            (
                plan_id,
                trip_id,
                request.total_budget,
                request.currency.upper(),
                json.dumps(breakdown),
            ),
        )
    return BudgetPlan(
        id=plan_id,
        trip_id=trip_id,
        total_budget=round(request.total_budget, 2),
        currency=request.currency.upper(),
        breakdown=breakdown,
    )


@app.get("/api/trips/{trip_id}/budget", response_model=BudgetPlan)
def get_trip_budget(trip_id: str, current_user=Depends(get_current_user)):
    find_user_trip(trip_id, current_user["id"])
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM budget_plans WHERE trip_id = ?", (trip_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Budget plan not found")
    return BudgetPlan(
        id=row["id"],
        trip_id=row["trip_id"],
        total_budget=row["total_budget"],
        currency=row["currency"],
        breakdown=json.loads(row["breakdown"]),
    )

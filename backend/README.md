# VoyageIQ Backend

This local MVP uses FastAPI and SQLite. It includes account registration and login, private trip management, and saved starter budget plans.

## Start the API

From PowerShell:

    cd C:\Users\weedc\VIQ\VoyageIQ\backend
    .\.venv\Scripts\Activate.ps1
    uvicorn app.main:app --reload --port 4000

The API documentation is at http://localhost:4000/docs and the health endpoint is at http://localhost:4000/api/health.

For local development, the server has a fallback secret. Before deploying, copy .env.example to .env and set JWT_SECRET to a long, unique secret. Do not commit .env.

To enable flight search, create a Self-Service app in the Amadeus for Developers portal and copy its test API key and secret into AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET in backend/.env. The test API base is already configured. Restart the server after changing .env.

## Use the protected trip endpoints

1. In /docs, register through POST /api/auth/register with a name, email, and password of at least eight characters.
2. Copy the returned token.
3. Click Authorize near the top of the docs page and paste the token, then authorize.
4. Create and manage trips. Each account can only read or change its own trips.

## Implemented routes

- GET /api/health
- GET /api/flights/search
- POST /api/auth/register
- POST /api/auth/login
- GET /api/trips
- POST /api/trips
- GET /api/trips/{trip_id}
- PUT /api/trips/{trip_id}
- DELETE /api/trips/{trip_id}
- POST /api/budget/calculate
- POST /api/trips/{trip_id}/budget
- GET /api/trips/{trip_id}/budget

The budget allocation is a starter estimate based on fixed percentages; it does not use live destination prices. Flight search uses Amadeus test or production credentials. Booking, notifications, and AI recommendations still need their own service integrations.

The database file is backend/voyageiq.db. The server creates the tables on startup and upgrades the original tutorial database without deleting its existing trip rows. Trips created before account support have no owner and therefore do not appear in an account's trip list.

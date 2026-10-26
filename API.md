# VoyageIQ API

Local development base URL: http://localhost:4000/api

Interactive API documentation: http://localhost:4000/docs

## Authentication

Register or log in to receive a bearer token. In /docs, click Authorize and enter the returned token before using protected routes. Tokens expire after 24 hours.

| Method | Route | Access | Purpose |
|---|---|---|---|
| POST | /api/auth/register | Public | Create an account with name, email, and password |
| POST | /api/auth/login | Public | Log in with email and password |

Passwords are hashed before storage. Trip and budget routes are scoped to the signed-in account.

## Health

| Method | Route | Purpose |
|---|---|---|
| GET | /api/health | Check whether the API is running |

## Flights

Flight search requires a Duffel test access token in `backend/.env` as `DUFFEL_ACCESS_TOKEN`. Requests use three-letter IATA airport or city codes. Duffel test mode uses simulated flight inventory and prices, so results are for development rather than real trip planning.

| Method | Route | Access | Purpose |
|---|---|---|---|
| GET | /api/flights/search | Public | Search offers with query fields from, to, date, optional returnDate, adults, children, nonStop, currencyCode, and max |

## Trips

Trip dates use ISO format (YYYY-MM-DD).

| Method | Route | Purpose |
|---|---|---|
| GET | /api/trips | List the signed-in user's trips |
| POST | /api/trips | Create a trip with title, destination, start_date, and end_date |
| GET | /api/trips/{trip_id} | Get one of the signed-in user's trips |
| PUT | /api/trips/{trip_id} | Replace a trip's title, destination, and dates |
| DELETE | /api/trips/{trip_id} | Delete a trip and its saved budget |

## Budgets

The budget calculator accepts destination, startDate, endDate, totalBudget, groupSize, and optional currency. It returns category allocations for flights, accommodation, food, activities, and local transport. The current allocation is a transparent starter estimate, not live pricing.

| Method | Route | Access | Purpose |
|---|---|---|---|
| POST | /api/budget/calculate | Public | Calculate a budget estimate |
| POST | /api/trips/{trip_id}/budget | Signed in | Save or replace the trip's budget plan |
| GET | /api/trips/{trip_id}/budget | Signed in | Read the saved budget plan |

## Errors

Errors use an object with an error message. Common status codes are 400 for invalid input, 401 for missing or invalid authentication, 404 for a record not found, 409 for an email already in use, and 422 for request fields that fail validation.

## Not implemented yet

Live flight search, price prediction, bookings, hotels, AI trip planning, and notifications require separate provider integrations and credentials. They are not simulated by this API.

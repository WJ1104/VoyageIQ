"""Asynchronous client for Duffel's test-mode flight search."""

import os

import httpx


class FlightProviderError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class DuffelClient:
    base_url = "https://api.duffel.com"

    def __init__(self):
        self.access_token = os.getenv("DUFFEL_ACCESS_TOKEN", "").strip()

    async def search_flights(self, parameters: dict) -> dict:
        if not self.access_token:
            raise FlightProviderError(
                "Flight search is not configured. Add DUFFEL_ACCESS_TOKEN to backend/.env.",
                status_code=503,
            )

        passengers = [{"type": "adult"} for _ in range(parameters["adults"])]
        # The existing route accepts a child count but not ages. Use age 8 as a
        # clear default for this MVP; airline child-fare rules can vary by age.
        passengers.extend({"age": 8} for _ in range(parameters.get("children", 0)))
        slices = [
            {
                "origin": parameters["originLocationCode"],
                "destination": parameters["destinationLocationCode"],
                "departure_date": parameters["departureDate"],
            }
        ]
        if parameters.get("returnDate"):
            slices.append(
                {
                    "origin": parameters["destinationLocationCode"],
                    "destination": parameters["originLocationCode"],
                    "departure_date": parameters["returnDate"],
                }
            )

        request_data = {
            "slices": slices,
            "passengers": passengers,
            "cabin_class": "economy",
        }
        if parameters.get("nonStop") == "true":
            request_data["max_connections"] = 0

        try:
            async with httpx.AsyncClient(timeout=35) as client:
                response = await client.post(
                    f"{self.base_url}/air/offer_requests?return_offers=true",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Duffel-Version": "v2",
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    json={"data": request_data},
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.TimeoutException as exc:
            raise FlightProviderError("Duffel flight search timed out", 504) from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise FlightProviderError(
                    "Duffel rejected the token. Check that backend/.env has a test token.", 502
                ) from exc
            if exc.response.status_code == 429:
                raise FlightProviderError("Duffel search limit reached; try again later", 503) from exc
            detail = "Duffel could not process this flight search"
            try:
                errors = exc.response.json().get("errors", [])
                if errors and isinstance(errors[0], dict):
                    detail = errors[0].get("message") or errors[0].get("title") or detail
            except (ValueError, AttributeError, TypeError):
                pass
            raise FlightProviderError(detail, 400 if exc.response.status_code == 400 else 502) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise FlightProviderError("Could not connect to Duffel flight search") from exc

        offers = payload.get("data", {}).get("offers", [])
        flights = [self._normalize_offer(offer) for offer in offers[: parameters.get("max", 20)]]
        currency = next(
            (flight["price"].get("currency") for flight in flights if flight["price"].get("currency")),
            parameters.get("currencyCode", "USD"),
        )
        return {"flights": flights, "currency": currency, "count": len(flights)}

    @staticmethod
    def _normalize_offer(offer: dict) -> dict:
        slices = []
        for flight_slice in offer.get("slices", []):
            segments = []
            for segment in flight_slice.get("segments", []):
                carrier = segment.get("marketing_carrier") or {}
                segments.append(
                    {
                        "carrierCode": carrier.get("iata_code"),
                        "carrierName": carrier.get("name") or carrier.get("iata_code"),
                        "flightNumber": segment.get("marketing_carrier_flight_number"),
                        "departure": {
                            "iataCode": (segment.get("origin") or {}).get("iata_code"),
                            "at": segment.get("departing_at"),
                        },
                        "arrival": {
                            "iataCode": (segment.get("destination") or {}).get("iata_code"),
                            "at": segment.get("arriving_at"),
                        },
                        "duration": segment.get("duration"),
                    }
                )
            slices.append(
                {
                    "duration": flight_slice.get("duration"),
                    "stops": max(len(segments) - 1, 0),
                    "segments": segments,
                }
            )

        owner = offer.get("owner") or {}
        return {
            "id": offer.get("id"),
            "price": {
                "currency": offer.get("total_currency"),
                "total": offer.get("total_amount"),
            },
            "bookableSeats": None,
            "validatingAirlineCodes": [owner["iata_code"]] if owner.get("iata_code") else [],
            "itineraries": slices,
            "providerOffer": offer,
        }


duffel_client = DuffelClient()

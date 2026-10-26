"""Small asynchronous client for Amadeus Self-Service flight search."""

import asyncio
import os
import time

import httpx


class FlightProviderError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class AmadeusClient:
    def __init__(self):
        self.base_url = os.getenv("AMADEUS_API_BASE_URL", "https://test.api.amadeus.com").rstrip("/")
        self.client_id = os.getenv("AMADEUS_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("AMADEUS_CLIENT_SECRET", "").strip()
        self._token: str | None = None
        self._token_expires_at = 0.0
        self._token_lock = asyncio.Lock()

    async def _access_token(self) -> str:
        if not self.client_id or not self.client_secret:
            raise FlightProviderError(
                "Flight search is not configured. Add Amadeus client keys to backend/.env.",
                status_code=503,
            )

        if self._token and time.monotonic() < self._token_expires_at:
            return self._token

        async with self._token_lock:
            if self._token and time.monotonic() < self._token_expires_at:
                return self._token
            try:
                async with httpx.AsyncClient(timeout=20) as client:
                    response = await client.post(
                        f"{self.base_url}/v1/security/oauth2/token",
                        data={
                            "grant_type": "client_credentials",
                            "client_id": self.client_id,
                            "client_secret": self.client_secret,
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
            except httpx.TimeoutException as exc:
                raise FlightProviderError("Amadeus authentication timed out", 504) from exc
            except httpx.HTTPStatusError as exc:
                raise FlightProviderError(
                    "Amadeus rejected the credentials; check the keys and API environment.", 502
                ) from exc
            except (httpx.HTTPError, ValueError) as exc:
                raise FlightProviderError("Could not connect to Amadeus authentication") from exc

            token = payload.get("access_token")
            if not token:
                raise FlightProviderError("Amadeus authentication returned no access token")
            lifetime = int(payload.get("expires_in", 1800))
            self._token = token
            self._token_expires_at = time.monotonic() + max(lifetime - 60, 1)
            return token

    async def search_flights(self, parameters: dict) -> dict:
        token = await self._access_token()
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/v2/shopping/flight-offers",
                    headers={"Authorization": f"Bearer {token}"},
                    params=parameters,
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.TimeoutException as exc:
            raise FlightProviderError("Amadeus flight search timed out", 504) from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 400:
                try:
                    detail = exc.response.json().get("errors", [{}])[0].get("detail")
                except (ValueError, IndexError, AttributeError):
                    detail = None
                raise FlightProviderError(detail or "Amadeus could not process this flight search", 400) from exc
            if exc.response.status_code == 429:
                raise FlightProviderError("Amadeus search limit reached; try again later", 503) from exc
            raise FlightProviderError("Amadeus flight search is temporarily unavailable", 502) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise FlightProviderError("Could not connect to Amadeus flight search") from exc

        dictionaries = payload.get("dictionaries", {})
        carriers = dictionaries.get("carriers", {})
        return {
            "flights": [self._normalize_offer(offer, carriers) for offer in payload.get("data", [])],
            "currency": parameters.get("currencyCode", "USD"),
            "count": len(payload.get("data", [])),
        }

    @staticmethod
    def _normalize_offer(offer: dict, carriers: dict) -> dict:
        itineraries = []
        for itinerary in offer.get("itineraries", []):
            segments = []
            for segment in itinerary.get("segments", []):
                carrier_code = segment.get("carrierCode", "")
                segments.append(
                    {
                        "carrierCode": carrier_code,
                        "carrierName": carriers.get(carrier_code, carrier_code),
                        "flightNumber": segment.get("number"),
                        "departure": segment.get("departure", {}),
                        "arrival": segment.get("arrival", {}),
                        "duration": segment.get("duration"),
                    }
                )
            itineraries.append(
                {
                    "duration": itinerary.get("duration"),
                    "stops": max(len(segments) - 1, 0),
                    "segments": segments,
                }
            )

        return {
            "id": offer.get("id"),
            "price": offer.get("price", {}),
            "bookableSeats": offer.get("numberOfBookableSeats"),
            "validatingAirlineCodes": offer.get("validatingAirlineCodes", []),
            "itineraries": itineraries,
            # Keep the provider offer available for a later price-confirmation step.
            "providerOffer": offer,
        }


amadeus_client = AmadeusClient()

"""EuroFuel API client."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientSession

from .models import Station, StationPrice


class EuroFuelApiClient:
    """Simple client for a EuroFuel-compatible station price API."""

    def __init__(self, session: ClientSession, base_url: str, api_key: str | None) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    async def async_get_stations(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_km: float,
        country_codes: list[str],
    ) -> list[Station]:
        """Fetch stations and fuel prices near a location."""
        headers: dict[str, str] = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        params = {
            "lat": latitude,
            "lon": longitude,
            "radius_km": radius_km,
            "country_codes": ",".join(country_codes),
        }

        async with self._session.get(
            f"{self._base_url}/stations", headers=headers, params=params, timeout=30
        ) as response:
            response.raise_for_status()
            payload = await response.json()

        return [self._parse_station(item) for item in payload.get("stations", [])]

    def _parse_station(self, item: dict[str, Any]) -> Station:
        """Parse station JSON payload."""
        prices: dict[str, StationPrice] = {}
        for fuel_type, fuel_payload in item.get("prices", {}).items():
            if fuel_payload.get("price") is None:
                continue
            prices[fuel_type.lower()] = StationPrice(
                fuel_type=fuel_type.lower(),
                price=float(fuel_payload["price"]),
                currency=fuel_payload.get("currency", "EUR"),
            )

        return Station(
            station_id=str(item["id"]),
            name=item.get("name", "Onbekend tankstation"),
            brand=item.get("brand"),
            address=item.get("address", "Adres onbekend"),
            latitude=float(item["location"]["lat"]),
            longitude=float(item["location"]["lon"]),
            country_code=item.get("country_code", "").upper(),
            prices=prices,
        )

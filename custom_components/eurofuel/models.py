"""Data models used by EuroFuel."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StationPrice:
    """Fuel price for a specific station and fuel type."""

    fuel_type: str
    price: float
    currency: str


@dataclass(slots=True)
class Station:
    """Station details with prices."""

    station_id: str
    name: str
    brand: str | None
    address: str
    latitude: float
    longitude: float
    country_code: str
    prices: dict[str, StationPrice]

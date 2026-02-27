"""Utility helpers for EuroFuel."""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from .const import FUEL_TYPES
from .models import Station


def find_cheapest(
    stations: list[Station], latitude: float, longitude: float
) -> dict[str, tuple[Station, float] | None]:
    """Find the cheapest station for each fuel type."""
    cheapest: dict[str, tuple[Station, float] | None] = {fuel_type: None for fuel_type in FUEL_TYPES}

    for station in stations:
        distance = distance_km(latitude, longitude, station.latitude, station.longitude)
        for fuel_type in FUEL_TYPES:
            price = station.prices.get(fuel_type)
            if price is None:
                continue
            current = cheapest[fuel_type]
            if current is None or price.price < current[0].prices[fuel_type].price:
                cheapest[fuel_type] = (station, distance)

    return cheapest


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in km."""
    radius_earth = 6371
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    )
    c = 2 * asin(sqrt(a))
    return radius_earth * c

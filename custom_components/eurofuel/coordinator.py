"""Data coordinator for EuroFuel."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.components.device_tracker.const import DOMAIN as DEVICE_TRACKER_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EuroFuelApiClient
from .const import (
    CONF_COUNTRY_CODES,
    CONF_DEVICE_TRACKER,
    CONF_FALLBACK_LATITUDE,
    CONF_FALLBACK_LONGITUDE,
    CONF_RADIUS_KM,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .models import Station
from .utils import distance_km, find_cheapest

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class EuroFuelData:
    """Coordinator data model."""

    latitude: float
    longitude: float
    stations: list[Station]
    cheapest: dict[str, tuple[Station, float] | None]


class EuroFuelCoordinator(DataUpdateCoordinator[EuroFuelData]):
    """Fetch and aggregate station prices."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, client: EuroFuelApiClient, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{config_entry.entry_id}",
            update_interval=config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        self._client = client

    async def _async_update_data(self) -> EuroFuelData:
        latitude, longitude = self._resolve_location()
        if latitude is None or longitude is None:
            raise UpdateFailed("Geen geldige locatie beschikbaar via device tracker of fallback coords")

        stations = await self.async_fetch_stations(
            latitude=latitude,
            longitude=longitude,
            radius_km=float(self.config_entry.options[CONF_RADIUS_KM]),
            country_codes=self.config_entry.options[CONF_COUNTRY_CODES],
        )
        cheapest = find_cheapest(stations, latitude, longitude)
        return EuroFuelData(latitude=latitude, longitude=longitude, stations=stations, cheapest=cheapest)

    async def async_fetch_stations(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_km: float,
        country_codes: list[str],
    ) -> list[Station]:
        """Fetch and sort stations by distance."""
        try:
            stations = await self._client.async_get_stations(
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
                country_codes=country_codes,
            )
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Kon EuroFuel data niet ophalen: {err}") from err

        return sorted(
            stations,
            key=lambda station: distance_km(latitude, longitude, station.latitude, station.longitude),
        )

    def _resolve_location(self) -> tuple[float | None, float | None]:
        tracker_entity_id = self.config_entry.options.get(CONF_DEVICE_TRACKER)
        if tracker_entity_id:
            location = self.resolve_tracker_location(self.hass, tracker_entity_id)
            if location:
                return location

        lat = self.config_entry.options.get(CONF_FALLBACK_LATITUDE)
        lon = self.config_entry.options.get(CONF_FALLBACK_LONGITUDE)
        if lat is not None and lon is not None:
            return float(lat), float(lon)

        return None, None

    @staticmethod
    def list_device_trackers(hass: HomeAssistant) -> list[str]:
        """List known device_tracker entities for UI selection."""
        entity_registry = er.async_get(hass)
        return sorted(
            entry.entity_id
            for entry in entity_registry.entities.values()
            if entry.domain == DEVICE_TRACKER_DOMAIN
        )

    @staticmethod
    def resolve_tracker_location(
        hass: HomeAssistant, tracker_entity_id: str
    ) -> tuple[float, float] | None:
        """Resolve latitude and longitude from device_tracker state."""
        state = hass.states.get(tracker_entity_id)
        if state is None:
            return None

        attr_lat = state.attributes.get("latitude")
        attr_lon = state.attributes.get("longitude")
        if attr_lat is None or attr_lon is None:
            return None

        return float(attr_lat), float(attr_lon)

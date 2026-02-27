"""Sensor platform for EuroFuel."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_EURO
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, FUEL_TYPES
from .coordinator import EuroFuelCoordinator
from .utils import distance_km


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EuroFuel sensors."""
    coordinator: EuroFuelCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [EuroFuelNearbyStationsSensor(coordinator, entry)]
    entities.extend(EuroFuelCheapestFuelSensor(coordinator, entry, fuel_type) for fuel_type in FUEL_TYPES)
    async_add_entities(entities)


class EuroFuelNearbyStationsSensor(CoordinatorEntity[EuroFuelCoordinator], SensorEntity):
    """Container sensor holding nearby station details."""

    _attr_has_entity_name = True
    _attr_name = "Nearby stations"
    _attr_icon = "mdi:gas-station"

    def __init__(self, coordinator: EuroFuelCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_nearby_stations"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.stations)

    @property
    def extra_state_attributes(self) -> dict:
        stations = []
        lat = self.coordinator.data.latitude
        lon = self.coordinator.data.longitude
        for station in self.coordinator.data.stations:
            stations.append(
                {
                    "id": station.station_id,
                    "name": station.name,
                    "brand": station.brand,
                    "address": station.address,
                    "country_code": station.country_code,
                    "distance_km": round(distance_km(lat, lon, station.latitude, station.longitude), 2),
                    "prices": {
                        fuel: {
                            "price": price.price,
                            "currency": price.currency,
                        }
                        for fuel, price in station.prices.items()
                    },
                }
            )

        return {
            "tracker_latitude": lat,
            "tracker_longitude": lon,
            "stations": stations,
        }


class EuroFuelCheapestFuelSensor(CoordinatorEntity[EuroFuelCoordinator], SensorEntity):
    """Cheapest station sensor for one fuel type."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = CURRENCY_EURO
    _attr_icon = "mdi:cash"

    def __init__(self, coordinator: EuroFuelCoordinator, entry: ConfigEntry, fuel_type: str) -> None:
        super().__init__(coordinator)
        self._fuel_type = fuel_type
        self._attr_unique_id = f"{entry.entry_id}_cheapest_{fuel_type}"
        self._attr_name = f"Cheapest {fuel_type.upper()}"

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.cheapest.get(self._fuel_type) is not None

    @property
    def native_value(self) -> float | None:
        cheapest = self.coordinator.data.cheapest.get(self._fuel_type)
        if cheapest is None:
            return None
        station = cheapest[0]
        return station.prices[self._fuel_type].price

    @property
    def extra_state_attributes(self) -> dict:
        cheapest = self.coordinator.data.cheapest.get(self._fuel_type)
        if cheapest is None:
            return {}
        station, distance_km = cheapest
        price = station.prices[self._fuel_type]
        return {
            "station_id": station.station_id,
            "station_name": station.name,
            "brand": station.brand,
            "address": station.address,
            "country_code": station.country_code,
            "distance_km": round(distance_km, 2),
            "currency": price.currency,
        }



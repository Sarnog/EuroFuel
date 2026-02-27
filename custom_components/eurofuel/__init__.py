"""EuroFuel integration for Home Assistant."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EuroFuelApiClient
from .const import (
    ATTR_ADDRESS,
    ATTR_BRAND,
    ATTR_COUNTRY_CODE,
    ATTR_CURRENCY,
    ATTR_DISTANCE_KM,
    ATTR_FUEL_TYPE,
    ATTR_PRICE,
    ATTR_STATION_ID,
    ATTR_STATION_NAME,
    CONF_API_BASE_URL,
    CONF_API_KEY,
    CONF_COUNTRY_CODES,
    CONF_DEVICE_TRACKER,
    CONF_FALLBACK_LATITUDE,
    CONF_FALLBACK_LONGITUDE,
    CONF_RADIUS_KM,
    DOMAIN,
    FUEL_TYPES,
    PLATFORMS,
    SERVICE_FIND_CHEAPEST,
)
from .coordinator import EuroFuelCoordinator
from .utils import find_cheapest

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_FUEL_TYPE): vol.In(FUEL_TYPES),
        vol.Optional(CONF_DEVICE_TRACKER): str,
        vol.Optional("latitude"): vol.Coerce(float),
        vol.Optional("longitude"): vol.Coerce(float),
        vol.Optional(CONF_RADIUS_KM): vol.Coerce(float),
        vol.Optional(CONF_COUNTRY_CODES): [str],
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EuroFuel from a config entry."""
    session = async_get_clientsession(hass)
    client = EuroFuelApiClient(
        session=session,
        base_url=entry.options[CONF_API_BASE_URL],
        api_key=entry.options.get(CONF_API_KEY),
    )
    coordinator = EuroFuelCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()

    domain_data = hass.data.setdefault(DOMAIN, {})
    domain_data[entry.entry_id] = coordinator

    if "service_registered" not in domain_data:
        hass.services.async_register(
            DOMAIN,
            SERVICE_FIND_CHEAPEST,
            _build_find_cheapest_service(hass),
            schema=SERVICE_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )
        domain_data["service_registered"] = True

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload EuroFuel entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    domain_data = hass.data[DOMAIN]
    domain_data.pop(entry.entry_id)

    active_entries = [key for key in domain_data if key != "service_registered"]
    if not active_entries and domain_data.get("service_registered"):
        hass.services.async_remove(DOMAIN, SERVICE_FIND_CHEAPEST)
        domain_data.pop("service_registered")

    return True


def _build_find_cheapest_service(hass: HomeAssistant):
    async def _async_handle_find_cheapest(call: ServiceCall) -> dict:
        coordinators = [
            coordinator
            for key, coordinator in hass.data.get(DOMAIN, {}).items()
            if key != "service_registered"
        ]
        if not coordinators:
            return {"error": "Geen actieve EuroFuel configuratie gevonden."}

        coordinator: EuroFuelCoordinator = coordinators[0]
        fuel_type = call.data[ATTR_FUEL_TYPE]

        location = _resolve_service_location(hass, coordinator, call)
        if location is None:
            return {"error": "Geen geldige locatie gevonden via service parameters of configuratie."}

        latitude, longitude = location
        radius_km = float(call.data.get(CONF_RADIUS_KM, coordinator.config_entry.options[CONF_RADIUS_KM]))
        country_codes = call.data.get(CONF_COUNTRY_CODES, coordinator.config_entry.options[CONF_COUNTRY_CODES])

        stations = await coordinator.async_fetch_stations(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            country_codes=country_codes,
        )
        cheapest = find_cheapest(stations, latitude, longitude).get(fuel_type)
        if cheapest is None:
            return {
                "fuel_type": fuel_type,
                "latitude": latitude,
                "longitude": longitude,
                "radius_km": radius_km,
                "country_codes": country_codes,
                "result": None,
            }

        station, distance = cheapest
        price = station.prices[fuel_type]
        return {
            "fuel_type": fuel_type,
            "latitude": latitude,
            "longitude": longitude,
            "radius_km": radius_km,
            "country_codes": country_codes,
            "result": {
                ATTR_STATION_ID: station.station_id,
                ATTR_STATION_NAME: station.name,
                ATTR_BRAND: station.brand,
                ATTR_ADDRESS: station.address,
                ATTR_COUNTRY_CODE: station.country_code,
                ATTR_DISTANCE_KM: round(distance, 2),
                ATTR_PRICE: price.price,
                ATTR_CURRENCY: price.currency,
            },
        }

    return _async_handle_find_cheapest


def _resolve_service_location(
    hass: HomeAssistant,
    coordinator: EuroFuelCoordinator,
    call: ServiceCall,
) -> tuple[float, float] | None:
    if "latitude" in call.data and "longitude" in call.data:
        return float(call.data["latitude"]), float(call.data["longitude"])

    tracker_entity_id = call.data.get(CONF_DEVICE_TRACKER) or coordinator.config_entry.options.get(CONF_DEVICE_TRACKER)
    if tracker_entity_id:
        location = EuroFuelCoordinator.resolve_tracker_location(hass, tracker_entity_id)
        if location:
            return location

    lat = coordinator.config_entry.options.get(CONF_FALLBACK_LATITUDE)
    lon = coordinator.config_entry.options.get(CONF_FALLBACK_LONGITUDE)
    if lat is not None and lon is not None:
        return float(lat), float(lon)

    return None

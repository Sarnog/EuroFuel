"""Constants for the EuroFuel integration."""

from datetime import timedelta

DOMAIN = "eurofuel"
PLATFORMS = ["sensor"]

CONF_API_BASE_URL = "api_base_url"
CONF_API_KEY = "api_key"
CONF_COUNTRY_CODES = "country_codes"
CONF_DEVICE_TRACKER = "device_tracker"
CONF_FALLBACK_LATITUDE = "fallback_latitude"
CONF_FALLBACK_LONGITUDE = "fallback_longitude"
CONF_RADIUS_KM = "radius_km"
CONF_SCAN_INTERVAL = "scan_interval"

ATTR_STATION_ID = "station_id"
ATTR_STATION_NAME = "station_name"
ATTR_BRAND = "brand"
ATTR_ADDRESS = "address"
ATTR_COUNTRY_CODE = "country_code"
ATTR_DISTANCE_KM = "distance_km"
ATTR_CURRENCY = "currency"
ATTR_PRICE = "price"
ATTR_FUEL_TYPE = "fuel_type"

SERVICE_FIND_CHEAPEST = "find_cheapest"

DEFAULT_NAME = "EuroFuel"
DEFAULT_RADIUS_KM = 15
DEFAULT_SCAN_INTERVAL = timedelta(minutes=10)
DEFAULT_API_BASE_URL = "https://api.eurofuel.example/v1"

FUEL_TYPES = ("e5", "e10", "diesel", "lpg")
EU_COUNTRY_CODES = (
    "AL", "AD", "AT", "BY", "BE", "BA", "BG", "HR", "CY", "CZ", "DK", "EE",
    "FI", "FR", "DE", "GR", "HU", "IS", "IE", "IT", "XK", "LV", "LI", "LT",
    "LU", "MT", "MD", "MC", "ME", "NL", "MK", "NO", "PL", "PT", "RO", "RU",
    "SM", "RS", "SK", "SI", "ES", "SE", "CH", "TR", "UA", "GB", "VA",
)

"""Config flow for EuroFuel."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_API_BASE_URL,
    CONF_API_KEY,
    CONF_COUNTRY_CODES,
    CONF_DEVICE_TRACKER,
    CONF_FALLBACK_LATITUDE,
    CONF_FALLBACK_LONGITUDE,
    CONF_RADIUS_KM,
    CONF_SCAN_INTERVAL,
    DEFAULT_API_BASE_URL,
    DEFAULT_NAME,
    DEFAULT_RADIUS_KM,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EU_COUNTRY_CODES,
)
from .coordinator import EuroFuelCoordinator


class EuroFuelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle EuroFuel config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            try:
                options = _normalize_user_input(user_input)
            except vol.Invalid:
                errors["base"] = "invalid_input"
            else:
                return self.async_create_entry(title=DEFAULT_NAME, data={}, options=options)

        return self.async_show_form(
            step_id="user", data_schema=await _build_schema(self.hass, user_input), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return EuroFuelOptionsFlow(config_entry)


class EuroFuelOptionsFlow(config_entries.OptionsFlow):
    """Handle options updates."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                options = _normalize_user_input(user_input)
            except vol.Invalid:
                errors["base"] = "invalid_input"
            else:
                return self.async_create_entry(title="", data=options)

        defaults = user_input or self._config_entry.options
        return self.async_show_form(
            step_id="init", data_schema=await _build_schema(self.hass, defaults), errors=errors
        )


async def _build_schema(hass, defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    tracker_entities = EuroFuelCoordinator.list_device_trackers(hass)

    return vol.Schema(
        {
            vol.Required(
                CONF_API_BASE_URL,
                default=defaults.get(CONF_API_BASE_URL, DEFAULT_API_BASE_URL),
            ): str,
            vol.Optional(
                CONF_API_KEY,
                default=defaults.get(CONF_API_KEY, ""),
            ): str,
            vol.Required(
                CONF_COUNTRY_CODES,
                default=",".join(defaults.get(CONF_COUNTRY_CODES, EU_COUNTRY_CODES)),
            ): str,
            vol.Optional(
                CONF_DEVICE_TRACKER,
                default=defaults.get(CONF_DEVICE_TRACKER, ""),
            ): vol.In([""] + tracker_entities),
            vol.Optional(
                CONF_FALLBACK_LATITUDE,
                default=defaults.get(CONF_FALLBACK_LATITUDE),
            ): vol.Any(None, vol.Coerce(float)),
            vol.Optional(
                CONF_FALLBACK_LONGITUDE,
                default=defaults.get(CONF_FALLBACK_LONGITUDE),
            ): vol.Any(None, vol.Coerce(float)),
            vol.Required(
                CONF_RADIUS_KM,
                default=defaults.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM),
            ): vol.All(vol.Coerce(float), vol.Range(min=1, max=200)),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=int(defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL).total_seconds() / 60),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=120)),
        }
    )


def _normalize_user_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Normalize and validate user options."""
    options = dict(user_input)
    options[CONF_COUNTRY_CODES] = _normalize_country_codes(options[CONF_COUNTRY_CODES])
    options[CONF_SCAN_INTERVAL] = timedelta(minutes=options[CONF_SCAN_INTERVAL])

    has_tracker = bool(options.get(CONF_DEVICE_TRACKER))
    has_fallback = (
        options.get(CONF_FALLBACK_LATITUDE) is not None
        and options.get(CONF_FALLBACK_LONGITUDE) is not None
    )
    if not has_tracker and not has_fallback:
        raise vol.Invalid(
            "Stel een device_tracker in of geef fallback latitude/longitude op."
        )

    return options


def _normalize_country_codes(raw_codes: str) -> list[str]:
    codes = sorted({part.strip().upper() for part in raw_codes.split(",") if part.strip()})
    invalid_codes = [code for code in codes if code not in EU_COUNTRY_CODES]
    if invalid_codes:
        raise vol.Invalid(f"Ongeldige Europese landcodes: {', '.join(invalid_codes)}")
    return codes

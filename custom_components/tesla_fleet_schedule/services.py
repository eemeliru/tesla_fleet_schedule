"""Services for Tesla Fleet Schedule."""

from __future__ import annotations

from datetime import time, timedelta
from typing import Any

import voluptuous as vol
from homeassistant.components.tesla_fleet.models import TeslaFleetData
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_DAYS_OF_WEEK,
    ATTR_ENABLED,
    ATTR_END_TIME,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_ONE_TIME,
    ATTR_SCHEDULE_ID,
    ATTR_START_TIME,
    ATTR_VEHICLE,
    DAY_BITS,
    DOMAIN,
    LOGGER,
    SERVICE_ADD_CHARGE_SCHEDULE,
    SERVICE_GET_CHARGE_SCHEDULE_DATA,
    SERVICE_REMOVE_CHARGE_SCHEDULE,
    SERVICE_WAKE_UP,
    TESLA_DOMAIN,
    WEEKDAY_NAMES,
)

TESLA_DEVICE_IDENTIFIER_PARTS = 2
LATITUDE_MIN = -90
LATITUDE_MAX = 90
LONGITUDE_MIN = -180
LONGITUDE_MAX = 180

ADD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_VEHICLE): cv.string,
        vol.Optional(ATTR_START_TIME): cv.time,
        vol.Optional(ATTR_END_TIME): cv.time,
        vol.Optional(ATTR_DAYS_OF_WEEK): vol.All(
            cv.ensure_list, [vol.In(WEEKDAY_NAMES)]
        ),
        vol.Optional(ATTR_ONE_TIME, default=True): cv.boolean,
        vol.Optional(ATTR_ENABLED, default=True): cv.boolean,
        vol.Optional(ATTR_SCHEDULE_ID): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional(ATTR_LATITUDE): vol.Coerce(float),
        vol.Optional(ATTR_LONGITUDE): vol.Coerce(float),
    }
)

REMOVE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_VEHICLE): cv.string,
        vol.Required(ATTR_SCHEDULE_ID): vol.All(vol.Coerce(int), vol.Range(min=0)),
    }
)

WAKE_UP_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_VEHICLE): cv.string,
    }
)

GET_CHARGE_SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_VEHICLE): cv.string,
    }
)


def _minutes(value: time) -> int:
    """Convert a Home Assistant time object to minutes after midnight."""
    return value.hour * 60 + value.minute


def _vehicle_from_device(hass: HomeAssistant, device_id: str) -> tuple[Any, str]:
    """Find a Tesla Fleet vehicle API object from a HA device ID."""
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        message = f"Unknown Home Assistant device: {device_id}"
        raise HomeAssistantError(message)

    vins = {
        identifier[1]
        for identifier in device.identifiers
        if identifier[0] == TESLA_DOMAIN
        and len(identifier) == TESLA_DEVICE_IDENTIFIER_PARTS
        and identifier[1]
    }
    if not vins:
        message = "The selected device is not a Tesla Fleet vehicle."
        raise HomeAssistantError(message)
    if len(vins) != 1:
        message = "The selected device maps to multiple Tesla VINs."
        raise HomeAssistantError(message)

    vin = next(iter(vins))

    for entry in hass.config_entries.async_entries(TESLA_DOMAIN):
        runtime = entry.runtime_data
        if not isinstance(runtime, TeslaFleetData):
            continue
        for vehicle in runtime.vehicles:
            if vehicle.vin == vin:
                return vehicle.api, vin

    message = (
        "The Tesla Fleet config entry containing the selected vehicle is not loaded."
    )
    raise HomeAssistantError(message)


async def _async_ensure_awake(_hass: HomeAssistant, vehicle: Any, vin: str) -> None:
    """Send a wake_up command to the vehicle via Tesla Fleet."""
    LOGGER.debug("Waking up %s", vin)
    try:
        await vehicle.wake_up()
    except Exception as err:
        message = f"Failed to wake up Tesla vehicle {vin}: {err}"
        raise HomeAssistantError(message) from err


def _get_location(hass: HomeAssistant, data: dict[str, Any]) -> tuple[float, float]:
    """Get schedule coordinates, defaulting to Home Assistant's configured location."""
    lat = data.get(ATTR_LATITUDE, hass.config.latitude)
    lon = data.get(ATTR_LONGITUDE, hass.config.longitude)

    if lat is None or lon is None:
        message = (
            "Latitude/longitude were not supplied and Home Assistant has no "
            "configured location."
        )
        raise HomeAssistantError(message)

    if not LATITUDE_MIN <= lat <= LATITUDE_MAX:
        message = "Latitude must be between -90 and 90."
        raise HomeAssistantError(message)
    if not LONGITUDE_MIN <= lon <= LONGITUDE_MAX:
        message = "Longitude must be between -180 and 180."
        raise HomeAssistantError(message)

    return float(lat), float(lon)


async def _async_add(call: ServiceCall) -> None:
    """Add a Tesla charging schedule."""
    data = call.data

    if ATTR_START_TIME not in data and ATTR_END_TIME not in data:
        message = "At least one of start_time or end_time must be supplied."
        raise HomeAssistantError(message)

    vehicle, vin = _vehicle_from_device(hass=call.hass, device_id=data[ATTR_VEHICLE])
    lat, lon = _get_location(call.hass, data)

    start_minutes = _minutes(data[ATTR_START_TIME]) if ATTR_START_TIME in data else None
    end_minutes = _minutes(data[ATTR_END_TIME]) if ATTR_END_TIME in data else None

    if data.get(ATTR_DAYS_OF_WEEK):
        days_of_week = 0
        for day in data[ATTR_DAYS_OF_WEEK]:
            days_of_week |= DAY_BITS[day]
    else:
        now = dt_util.now()
        now_minutes = now.hour * 60 + now.minute
        reference_minutes = start_minutes if start_minutes is not None else end_minutes

        if reference_minutes is not None and reference_minutes > now_minutes:
            target_date = now.date()
        else:
            target_date = (now + timedelta(days=1)).date()

        days_of_week = DAY_BITS[WEEKDAY_NAMES[target_date.weekday()]]

    kwargs: dict[str, Any] = {
        "days_of_week": days_of_week,
        "enabled": data[ATTR_ENABLED],
        "lat": lat,
        "lon": lon,
        "one_time": data[ATTR_ONE_TIME],
    }
    if start_minutes is not None:
        kwargs["start_time"] = start_minutes
    if end_minutes is not None:
        kwargs["end_time"] = end_minutes

    if ATTR_SCHEDULE_ID in data:
        kwargs["id"] = data[ATTR_SCHEDULE_ID]

    try:
        result = await vehicle.add_charge_schedule(**kwargs)
    except Exception as err:
        LOGGER.exception("Failed to add Tesla charge schedule for %s", vin)
        message = f"Tesla charge schedule command failed for {vin}: {err}"
        raise HomeAssistantError(message) from err

    LOGGER.debug("Tesla charge schedule result for %s: %s", vin, result)


async def _async_remove(call: ServiceCall) -> None:
    """Remove a Tesla charging schedule."""
    data = call.data
    vehicle, vin = _vehicle_from_device(hass=call.hass, device_id=data[ATTR_VEHICLE])

    try:
        result = await vehicle.remove_charge_schedule(data[ATTR_SCHEDULE_ID])
    except Exception as err:
        LOGGER.exception("Failed to remove Tesla charge schedule for %s", vin)
        message = f"Tesla charge schedule removal failed for {vin}: {err}"
        raise HomeAssistantError(message) from err

    LOGGER.debug("Tesla charge schedule removal result for %s: %s", vin, result)


async def _async_wake_up(call: ServiceCall) -> None:
    """Send a wake_up command to a Tesla vehicle via Tesla Fleet."""
    data = call.data
    vehicle, vin = _vehicle_from_device(hass=call.hass, device_id=data[ATTR_VEHICLE])
    await _async_ensure_awake(call.hass, vehicle, vin)


async def _async_get_charge_schedule(call: ServiceCall) -> ServiceResponse:
    """Fetch charge_schedule_data for a Tesla vehicle via vehicle_data."""
    data = call.data
    vehicle, vin = _vehicle_from_device(hass=call.hass, device_id=data[ATTR_VEHICLE])

    try:
        result = await vehicle.vehicle_data(endpoints=["charge_schedule_data"])
    except Exception as err:
        LOGGER.exception("Failed to get Tesla charge_schedule_data for %s", vin)
        message = f"Tesla vehicle_data request failed for {vin}: {err}"
        raise HomeAssistantError(message) from err

    charge_schedule_data = result.get("response", {}).get("charge_schedule_data", {})
    LOGGER.debug("Tesla charge_schedule_data for %s: %s", vin, charge_schedule_data)

    return charge_schedule_data


def async_setup_services(hass: HomeAssistant) -> None:
    """Register Tesla Fleet Schedule services."""
    canonical_services = (
        (SERVICE_ADD_CHARGE_SCHEDULE, _async_add, ADD_SCHEMA),
        (SERVICE_REMOVE_CHARGE_SCHEDULE, _async_remove, REMOVE_SCHEMA),
        (SERVICE_WAKE_UP, _async_wake_up, WAKE_UP_SCHEMA),
        (
            SERVICE_GET_CHARGE_SCHEDULE_DATA,
            _async_get_charge_schedule,
            GET_CHARGE_SCHEDULE_SCHEMA,
        ),
    )
    for service_name, handler, schema in canonical_services:
        hass.services.async_register(
            DOMAIN,
            service_name,
            handler,
            schema=schema,
            supports_response=(
                SupportsResponse.ONLY
                if service_name == SERVICE_GET_CHARGE_SCHEDULE_DATA
                else None
            ),
        )


def async_unload_services(hass: HomeAssistant) -> None:
    """Remove Tesla Fleet Schedule services."""
    for service in (
        SERVICE_ADD_CHARGE_SCHEDULE,
        SERVICE_REMOVE_CHARGE_SCHEDULE,
        SERVICE_WAKE_UP,
        SERVICE_GET_CHARGE_SCHEDULE_DATA,
    ):
        hass.services.async_remove(DOMAIN, service)

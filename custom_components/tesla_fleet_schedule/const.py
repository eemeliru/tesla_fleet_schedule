"""Constants for Tesla Fleet Schedule."""

from __future__ import annotations

from logging import Logger, getLogger

DOMAIN = "tesla_fleet_schedule"
TESLA_DOMAIN = "tesla_fleet"
LOGGER: Logger = getLogger(__package__)

SERVICE_ADD_CHARGE_SCHEDULE = "add_charge_schedule"
SERVICE_REMOVE_CHARGE_SCHEDULE = "remove_charge_schedule"
SERVICE_WAKE_UP = "wake_up"
SERVICE_GET_CHARGE_SCHEDULE_DATA = "get_charge_schedule_data"

ATTR_VEHICLE = "vehicle"
ATTR_START_TIME = "start_time"
ATTR_END_TIME = "end_time"
ATTR_DAYS_OF_WEEK = "days_of_week"
ATTR_ONE_TIME = "one_time"
ATTR_ENABLED = "enabled"
ATTR_SCHEDULE_ID = "schedule_id"
ATTR_LATITUDE = "latitude"
ATTR_LONGITUDE = "longitude"

WEEKDAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

DAY_BITS = {
    "Sunday": 1,
    "Monday": 2,
    "Tuesday": 4,
    "Wednesday": 8,
    "Thursday": 16,
    "Friday": 32,
    "Saturday": 64,
}
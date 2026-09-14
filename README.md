# Tesla Fleet Schedule for Home Assistant

Custom integration for Home Assistant 2026.9.x, which exposes Tesla Fleet API charge scheduling as 
Home Assistant services while
reusing the authenticated vehicle objects 
from the official `tesla_fleet` integration.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add `https://github.com/eemeliru/tesla_fleet_schedule` as repository and select "Integration" as category
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/tesla_fleet_schedule` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

### After restart
Add **Tesla Fleet Schedule** from
**Settings -> Devices & services -> Add integration**.

## Services

This integration provides the Tesla Fleet API-aligned service names under the `tesla_fleet_schedule` domain:

- `add_charge_schedule`: add or update a charge schedule.
- `remove_charge_schedule`: remove a charge schedule by Tesla schedule ID.
- `wake_up`: send `wake_up` through the official Tesla Fleet integration.
- `get_charge_schedule_data`: fetch `charge_schedule_data` and return it as service
  response data.

### add_charge_schedule

Adds a new charging schedule, or updates an existing schedule. 
The `vehicle` must be a device provided by the
official Tesla Fleet integration.

Parameters:

- `vehicle` (**required**): Tesla vehicle device to configure.
- `start_time` (optional): Local vehicle time when charging should start, in
  `HH:MM` format.
- `end_time` (optional): Local vehicle time when charging should end, in
  `HH:MM` format.
- `days_of_week` (optional): One or more weekdays from `Monday` through
  `Sunday`. If omitted or empty, the service selects the next occurrence of
  the supplied `start_time`, or `end_time` when no start time is supplied. It
  selects today when that time is still ahead; otherwise it selects tomorrow.
- `one_time` (optional, default `true`): Whether the schedule runs only once.
  Set to `false` for a repeating schedule.
- `enabled` (optional, default `true`): Whether the schedule is enabled.
- `schedule_id` (optional): Existing Tesla schedule ID to update. Omit it to
  create a new schedule. **NOTE**: You can't delete schedules create by API
  call in Tesla phone app, so it's highly recommended to re-use same id's when
  sending schedule's via this integration.
- `latitude` (optional): Latitude of the location where the schedule applies.
  Defaults to Home Assistant's configured latitude.
- `longitude` (optional): Longitude of the location where the schedule
  applies. Defaults to Home Assistant's configured longitude.

At least one of `start_time` or `end_time` is required. If latitude or
longitude is omitted, the corresponding Home Assistant location value is
used; both values must be available and within the normal coordinate ranges.
Latitude & longitude are required by Fleet API.

### remove_charge_schedule

Removes a charging schedule from the selected vehicle.

Parameters:

- `vehicle` (**required**): Tesla vehicle device containing the schedule.
- `schedule_id` (**required**): Tesla schedule ID to remove.

### wake_up

Sends a `wake_up` command to the selected vehicle through the official Tesla
Fleet integration. This service does not wait for the vehicle to become
online or check its resulting state.
Call it before `add`/`remove` if your vehicle might be asleep or
offline, and use your own automation (e.g. wait for a Tesla Fleet, TeslaMate,
or other state entity to report online) to decide when to proceed. 
Alternately just wait for x seconds for vehicle to wake up, but note that 
[Tesla wake-up time is inconsistent](https://developer.tesla.com/docs/fleet-api/getting-started/best-practices#ensure-connectivity-state-before-interacting-with-a-device).

Parameters:

- `vehicle` (**required**): Tesla vehicle device to wake up.

### get_charge_schedule_data

Fetches the vehicle's current `charge_schedule_data` through the Tesla Fleet
`vehicle_data` endpoint. The service returns the fetched data as response
data; I have only used this to find schedule_id for `remove_charge_schedule`.

Parameters:

- `vehicle` (**required**): Tesla vehicle device to query.


## Dependencies

The official Tesla Fleet integration in Home Assistant 2026.9.0 requires
`tesla-fleet-api==1.10.0`. That version exposes `VehicleFleet.add_charge_schedule`
and `remove_charge_schedule`, so this component does not need to install or
replace the library. Not tested on earlier Home Assistant / tesla-fleet-api versions.

This component intentionally imports the official integration's internal
`TeslaFleetData` model. That is what lets it reuse the existing authenticated
client and signing/key setup without asking you for another Tesla token.

## Development

Install development dependencies:

```bash
python3 -m pip install -r requirements_common.txt
python3 -m pip install -r requirements_dev.txt
```

Start Home Assistant for local development:

```bash
scripts/develop
```

Run local checks:

```bash
python3 -m compileall custom_components/tesla_fleet_schedule
python3 -m ruff check .
python3 -m ruff format . --check
```

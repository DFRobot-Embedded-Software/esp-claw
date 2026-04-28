# Lua Environmental Sensor

This module describes how to read environmental data from Lua using the
Bosch BME690 backend. It exposes temperature, pressure, humidity, and gas
resistance readings through a simple blocking API.

## How to call
- Import it with `local environmental_sensor = require("environmental_sensor")`
- Open the sensor with one of:
  - `local sensor = environmental_sensor.new()` — use board defaults from `environmental_sensor`
  - `local sensor = environmental_sensor.new("environmental_sensor")` — choose a device name explicitly
  - `local sensor = environmental_sensor.new({ peripheral = "i2c_master" })` — provide options directly
  - `local sensor = environmental_sensor.new("environmental_sensor", { i2c_addr = 0x77 })` — board defaults + per-field overrides
- Read all values with `local sample = sensor:read()`
- Or read one value at a time:
  - `sensor:read_temperature()`
  - `sensor:read_pressure()`
  - `sensor:read_humidity()`
  - `sensor:read_gas()`
- Inspect sensor identity with:
  - `sensor:name()`
  - `sensor:chip_id()`
  - `sensor:variant_id()`
- Call `sensor:close()` when needed

## Options table
All fields are optional. Any field omitted falls back to the board
`board_devices.yaml` value for the selected device name (default
`"environmental_sensor"`). If that default device is not declared, the
module also tries the legacy name `"bme690_sensor"`.

| Field              | Type    | Meaning                                                         |
|--------------------|---------|-----------------------------------------------------------------|
| `device`           | string  | Board device name to load defaults from                         |
| `peripheral`       | string  | Board I2C master peripheral name, e.g. `"i2c_master"`          |
| `i2c_addr`         | integer | BME690 7-bit I2C address, `0x76` or `0x77`                     |
| `frequency`        | integer | I2C clock in Hz (default `400000`)                             |
| `heater_temp`      | integer | Heater target temperature in Celsius (default `300`)           |
| `heater_duration`  | integer | Heater duration in milliseconds (default `100`)                |

## Data format
- `sample.temperature` — degrees Celsius
- `sample.pressure` — pressure in Pa
- `sample.humidity` — relative humidity in percent
- `sample.gas_resistance` — gas resistance in ohms
- `sample.status` — raw BME690 status flags
- `sample.gas_index` — gas measurement index from the driver
- `sample.meas_index` — measurement index from the driver

## Example
```lua
local environmental_sensor = require("environmental_sensor")

local sensor = environmental_sensor.new()
local sample = sensor:read()

print(string.format("temperature: %.2f C", sample.temperature))
print(string.format("pressure: %.2f Pa", sample.pressure))
print(string.format("humidity: %.2f %%", sample.humidity))
print(string.format("gas resistance: %.2f ohm", sample.gas_resistance))
print(string.format("status: 0x%02X", sample.status))

sensor:close()
```

## Notes
- Reads are blocking. Each call triggers a forced-mode BME690 measurement.
- The board device must resolve to a valid I2C peripheral, or you must pass
  `peripheral` explicitly in Lua.
- Any setup or read failure raises a Lua error.

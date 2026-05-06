# Lua DHT

This module describes how to read temperature and humidity from DHT-family
single-wire sensors in Lua. It wraps the underlying `dht` driver and
exposes simple blocking read helpers for common sensor types.

## How to call
- Import it with `local dht = require("dht")`
- Read decoded values with `local temp_c, humidity = dht.read(gpio, sensor_type)`
- Read raw sensor values with `local temp_raw, humidity_raw = dht.read_raw(gpio, sensor_type)`
- `gpio`: GPIO number connected to the sensor data pin
- `sensor_type`: optional string, defaults to `dht.TYPE_DHT11`

## Sensor types
- `dht.TYPE_DHT11` -> `"dht11"`
- `dht.TYPE_DHT22` -> `"dht22"`
- `dht.TYPE_SI7021` -> `"si7021"`

The module also accepts these sensor type strings:
- `"dht11"`
- `"dht22"`, `"am2301"`, `"am2302"`, `"am2321"`, `"dht21"`
- `"si7021"`

Passing any other string raises a Lua error.

## Return values
- `dht.read(gpio, sensor_type)` returns two Lua numbers:
  - `temp_c`: temperature in degrees Celsius
  - `humidity`: relative humidity in percent
- `dht.read_raw(gpio, sensor_type)` returns two Lua integers from the raw driver API:
  - `temp_raw`
  - `humidity_raw`

If the driver read fails, the call raises a Lua error such as
`dht_read_float_data failed: <reason>` or `dht_read_data failed: <reason>`.

## Example
```lua
local dht = require("dht")

local temp_c, humidity = dht.read(4, dht.TYPE_DHT22)
print(string.format("temp=%.1fC humidity=%.1f%%", temp_c, humidity))
```

## Notes
- Reads are blocking and should be used at a modest polling rate.
- The sensor data line must be wired to a GPIO that matches your board setup.
- This module does not manage sensor power or background sampling.

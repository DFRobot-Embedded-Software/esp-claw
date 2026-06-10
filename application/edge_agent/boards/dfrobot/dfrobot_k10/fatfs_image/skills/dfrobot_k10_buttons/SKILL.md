---
{
  "name": "dfrobot_k10_buttons",
  "description": "Detect or read the DFRobot K10 onboard buttons KA and KB (press, click, key state). Use when the user asks about K10 button input. Requires board_hardware_info skill.",
  "metadata": {
    "cap_groups": [
      "cap_lua"
    ],
    "manage_mode": "readonly"
  }
}
---

# DFRobot K10 Buttons (KA / KB)

Use this skill when the user asks to detect, read, or react to the K10 onboard buttons KA or KB.

## Hardware Facts

The K10 buttons are wired to a TCA9555 (XL9555) I2C IO expander, **NOT** to ESP32 GPIOs.

| Button | Expander linear pin | Chip silkscreen pin | Active level |
|--------|---------------------|---------------------|--------------|
| KB     | 2                   | P02                 | 0 (low = pressed) |
| KA     | 12                  | P14                 | 0 (low = pressed) |

The expander is the Board Manager device named `gpio_expander`.

## Rules

- NEVER call `button.new(...)` for KA/KB. The Lua `button` module only supports ESP32 GPIOs.
- NEVER scan or probe ESP32 GPIOs to find these buttons.
- Pin numbers above are expander pins. Expander pin `12` is NOT ESP32 `GPIO12` (GPIO12 is the LCD SPI clock on this board).
- Read button state only with `board_manager.get_gpio_expander_level("gpio_expander", pin)`.
- If `lua_run_script` returns an error, report it directly to the user. Do not retry with changed arguments.

## How To Read The Buttons

```lua
local board_manager = require("board_manager")

-- level: 1 = released, 0 = pressed (active-low)
local kb_level = board_manager.get_gpio_expander_level("gpio_expander", 2)
local ka_level = board_manager.get_gpio_expander_level("gpio_expander", 12)
```

Polling loop example (detect a single KB press, exit after detection or timeout):

```lua
local board_manager = require("board_manager")

local deadline = os.clock() + 10  -- seconds
while os.clock() < deadline do
    local level = board_manager.get_gpio_expander_level("gpio_expander", 2)
    if level == 0 then
        print("KB pressed")
        break
    end
    os.sleep(0.05)
end
```

Poll at 20 Hz or slower (sleep >= 0.05 s) to avoid I2C bus contention with the camera and audio codec on the same bus.

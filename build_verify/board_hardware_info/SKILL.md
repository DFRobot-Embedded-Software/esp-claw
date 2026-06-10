---
{
  "name": "board_hardware_info",
  "description": "Use this skill before operating hardware or writing Lua and board-specific code that depends on device inventory and occupied GPIOs.",
  "metadata": {
    "cap_groups": ["cap_boards"],
    "manage_mode": "readonly"
  }
}
---

# Current Board Hardware: dfrobot_k10

Read this skill before operating hardware, assigning GPIOs, or writing Lua and board-specific code. **You cannot speculate or fabricate hardware information.**

## Rules
- Before operating any hardware, read this skill first.
- Before assigning a GPIO, check whether it is already occupied below.
- When writing Lua or board-specific code, use the listed device names instead of guessing hardware wiring.
- IO-expander buttons are **not** ESP32 GPIO buttons. Never call `button.new(N)` or scan ESP32 GPIOs for them. Use `board_manager.get_gpio_expander_level("gpio_expander", pin)` instead (`pin` is the expander linear pin below).

## Board Summary
- Board: `dfrobot_k10`
- Chip: `esp32s3`
- Version: `1`
- Manufacturer: `unknown`

## Device Inventory

The following devices are known to be present on this board:

### gpio_expander
- Occupied IO:
  - `sda` -> `GPIO47`
  - `scl` -> `GPIO48`

### button_kb
- Occupied IO:
  - `gpio_expander`: `tca9555` expander linear pin `2` (chip pin `P02`), not ESP32 GPIO
  - active_level -> `0`

### button_ka
- Occupied IO:
  - `gpio_expander`: `tca9555` expander linear pin `12` (chip pin `P14`), not ESP32 GPIO
  - active_level -> `0`

### audio_dac
- Occupied IO:
  - `mclk` -> `GPIO3`
  - `bclk` -> `GPIO0`
  - `ws` -> `GPIO38`
  - `dout` -> `GPIO45`
  - `din` -> `GPIO39`

### audio_adc
- Occupied IO:
  - `mclk` -> `GPIO3`
  - `bclk` -> `GPIO0`
  - `ws` -> `GPIO38`
  - `dout` -> `GPIO45`
  - `din` -> `GPIO39`
  - `sda` -> `GPIO47`
  - `scl` -> `GPIO48`

### camera
- Occupied IO:
  - `vsync` -> `GPIO4`
  - `de` -> `GPIO5`
  - `pclk` -> `GPIO17`
  - `xclk` -> `GPIO7`
  - `sda` -> `GPIO47`
  - `scl` -> `GPIO48`

### display_lcd
- Occupied IO:
  - `cs` -> `GPIO14`
  - `dc` -> `GPIO13`
  - `mosi` -> `GPIO21`
  - `sclk` -> `GPIO12`

### led_strip
- Occupied IO:
  - `gpio` -> `GPIO46`

## Notes
- If a device has no explicit IO mapping here, treat it as unknown instead of guessing.

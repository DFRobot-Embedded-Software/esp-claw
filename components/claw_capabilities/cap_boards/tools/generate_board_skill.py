#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2026 Espressif Systems (Shanghai) CO LTD
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


PIN_KEY_SUFFIXES = (
    '_io_num',
    '_gpio_num',
    '_io',
)
PIN_KEY_NAMES = {
    'gpio_num',
    'pin',
    'sda',
    'scl',
    'mclk',
    'bclk',
    'ws',
    'mosi',
    'miso',
    'sclk',
    'clk',
    'dout',
    'din',
    'cs',
    'dc',
    'reset',
    'vsync',
    'hsync',
    'de',
    'pclk',
    'xclk',
    'pwdn',
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Generate current board skill markdown.')
    parser.add_argument('--metadata-yaml', required=True, help='Path to gen_board_metadata.yaml')
    parser.add_argument('--output-md', required=True, help='Generated markdown output path')
    return parser.parse_args()


def load_metadata(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise RuntimeError(f'Missing generated board metadata file: {path}') from exc
    if not isinstance(data, dict):
        raise RuntimeError(f'Expected generated board metadata to be a YAML mapping: {path}')
    return data


def normalize_label(path_parts: list[str]) -> str:
    filtered = [part for part in path_parts if part not in {'io', 'pins'}]
    if not filtered:
        filtered = path_parts
    normalized_parts = []
    for part in filtered:
        normalized = part.replace('_io_num', '').replace('_gpio_num', '').replace('_io', '')
        if normalized == 'gpio_num':
            normalized = 'gpio'
        normalized_parts.append(normalized)
    return '.'.join(part for part in normalized_parts if part)


def is_pin_key(key: str, parents: list[str]) -> bool:
    if parents and parents[-1] == 'levels':
        return False
    return key in PIN_KEY_NAMES or key.endswith(PIN_KEY_SUFFIXES) or (parents and parents[-1] in {'io', 'pins'})


def collect_io_entries(node: Any, path_parts: list[str] | None = None) -> list[tuple[str, int]]:
    path_parts = path_parts or []
    entries: list[tuple[str, int]] = []

    if isinstance(node, dict):
        for key, value in node.items():
            current_path = path_parts + [str(key)]
            if type(value) is int and value >= 0 and is_pin_key(str(key), path_parts):
                entries.append((normalize_label(current_path), value))
                continue
            if isinstance(value, list) and key == 'data_io':
                for index, item in enumerate(value):
                    if type(item) is int and item >= 0:
                        entries.append((f'{normalize_label(current_path)}[{index}]', item))
                continue
            entries.extend(collect_io_entries(value, current_path))
        return entries

    if isinstance(node, list):
        for index, item in enumerate(node):
            entries.extend(collect_io_entries(item, path_parts + [str(index)]))
    return entries


def format_io_list(entries: list[tuple[str, int]]) -> list[str]:
    seen: set[tuple[str, int]] = set()
    lines: list[str] = []
    for label, pin in entries:
        key = (label, pin)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f'- `{label}` -> `GPIO{pin}`')
    return lines


def format_device_io_lines(io: Any) -> list[str]:
    if not isinstance(io, dict):
        return format_io_list(collect_io_entries(io))

    lines: list[str] = []
    routed_via = io.get('routed_via')
    expander_io = io.get('expander_io')
    if isinstance(routed_via, str) and isinstance(expander_io, int):
        expander_chip = io.get('expander_chip')
        chip_pin = io.get('chip_pin')
        chip_label = f'`{expander_chip}` ' if isinstance(expander_chip, str) else ''
        pin_label = f' (chip pin `{chip_pin}`)' if isinstance(chip_pin, str) else ''
        lines.append(
            f'- `{routed_via}`: {chip_label}expander linear pin `{expander_io}`{pin_label}, '
            f'not ESP32 GPIO'
        )
    if 'active_level' in io:
        lines.append(f'- active_level -> `{io["active_level"]}`')

    for line in format_io_list(collect_io_entries(io)):
        if 'expander_io' in io and line.startswith('- `expander`'):
            continue
        lines.append(line)
    return list(dict.fromkeys(lines))


def load_devices(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    raw_devices = metadata.get('devices', {})
    raw_peripherals = metadata.get('peripherals', {})
    if not isinstance(raw_devices, dict):
        raise RuntimeError('Expected devices to be a YAML mapping')
    if not isinstance(raw_peripherals, dict):
        raise RuntimeError('Expected peripherals to be a YAML mapping')

    devices: list[dict[str, Any]] = []
    for name, config in raw_devices.items():
        if not isinstance(name, str) or name.startswith('fake'):
            continue
        if not isinstance(config, dict):
            config = {}

        io_lines = format_device_io_lines(config.get('io', {}))
        peripherals: list[dict[str, Any]] = []
        for peripheral_name in config.get('peripherals', []) or []:
            peripheral_config = raw_peripherals.get(peripheral_name, {})
            peripherals.append({
                'name': str(peripheral_name),
                'io_lines': format_device_io_lines(
                    peripheral_config.get('io', {}) if isinstance(peripheral_config, dict) else {}
                ),
            })

        devices.append({
            'name': name,
            'io_lines': io_lines,
            'peripherals': peripherals,
        })
    return devices


def render_markdown(metadata: dict[str, Any], devices: list[dict[str, Any]]) -> str:
    board_name = str(metadata.get('board', 'unknown'))
    chip = str(metadata.get('chip', 'unknown'))
    version = str(metadata.get('version', 'unknown'))
    manufacturer = str(metadata.get('manufacturer', 'unknown'))
    description = str(metadata.get('description', ''))
    lines = [
        '---',
        '{',
        '  "name": "board_hardware_info",',
        '  "description": "Use this skill before operating hardware or writing Lua and board-specific code that depends on device inventory '
        'and occupied GPIOs.",',
        '  "metadata": {',
        '    "cap_groups": ["cap_boards"],',
        '    "manage_mode": "readonly"',
        '  }',
        '}',
        '---',
        '',
        f'# Current Board Hardware: {board_name}',
        '',
        'Read this skill before operating hardware, assigning GPIOs, or writing Lua and board-specific code. **You cannot speculate or fabricate hardware information.**',
        '',
        '## Rules',
        '- Before operating any hardware, read this skill first.',
        '- Before assigning a GPIO, check whether it is already occupied below.',
        '- When writing Lua or board-specific code, use the listed device names instead of guessing hardware wiring.',
        '- IO-expander buttons are **not** ESP32 GPIO buttons. Never call `button.new(N)` or scan ESP32 GPIOs for them. '
        'Use `board_manager.get_gpio_expander_level("gpio_expander", pin)` instead (`pin` is the expander linear pin below).',
        '',
        '## Board Summary',
        f'- Board: `{board_name}`',
        f'- Chip: `{chip}`',
        f'- Version: `{version}`',
        f'- Manufacturer: `{manufacturer}`',
    ]

    if description:
        lines.append(f'- Description: {description}')

    lines.extend([
        '',
        '## Device Inventory',
        '',
        'The following devices are known to be present on this board:',
    ])

    for device in devices:
        lines.extend(['', f"### {device['name']}"])
        io_lines = list(device['io_lines'])
        for peripheral in device['peripherals']:
            io_lines.extend(peripheral['io_lines'])
        io_lines = list(dict.fromkeys(io_lines))

        if io_lines:
            lines.append('- Occupied IO:')
            lines.extend([f'  {line}' for line in io_lines])
        else:
            lines.append('- Occupied IO: none declared')

    lines.extend([
        '',
        '## Notes',
        '- If a device has no explicit IO mapping here, treat it as unknown instead of guessing.',
        '',
    ])
    return '\n'.join(lines)


def main() -> int:
    args = parse_args()
    metadata_yaml = Path(args.metadata_yaml).resolve()
    output_md = Path(args.output_md).resolve()

    print(f'[cap_boards] Loading generated board metadata from {metadata_yaml}')
    metadata = load_metadata(metadata_yaml)
    devices = load_devices(metadata)
    markdown = render_markdown(metadata, devices)

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(markdown, encoding='utf-8')
    print(
        f"[cap_boards] Generated skill for board {metadata.get('board', 'unknown')} "
        f'with {len(devices)} devices: {output_md}'
    )
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f'generate_board_skill.py: {exc}', file=sys.stderr)
        raise SystemExit(1)

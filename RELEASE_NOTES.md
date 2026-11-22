# v0.1.0 — First release

First public release of the Delios Home Assistant custom integration.

## What's new

- UI config flow: enter your inverter's host and credentials, validated on setup.
- Local polling of the device REST API (30s default, configurable).
- Sensors for live power (PV, battery, grid, house), string V/I, battery SOC, self-consumption, lifetime energy totalizers, firmware versions, WiFi/LAN/USB status, and the last alarm code.
- Binary sensors for inverter, PV, battery, DDI, and Li alarms (plus Li warning).
- Everything grouped under one "Delios Inverter" device.
- Brand icon and logo included.

## Installation

**HACS (recommended):** add `https://github.com/reschandreas/delios-homeassistant` as a custom repository (Integration category), install, restart, then add via UI.

**Manual:** copy `custom_components/delios` into `config/custom_components/`, restart, add via UI.

## Configuration

- Host: your inverter's IP or hostname.
- Username/password: factory defaults are `user/user`, `installer/installer`, `service/service`. Use `service` for full access.

## Security notes

The device ships with default credentials and no forced change, so change the password after pairing. Polling is read-only — the integration won't touch your inverter settings.

## Compatibility

Home Assistant Core 2024.x or newer (tested on 2026.11.2). Python 3.12+.

## License

MIT

## Acknowledgements

Reverse-engineered from the device's own web interface (Delios Srl hybrid inverter, firmware 1.0.05). Not affiliated with Delios Srl.
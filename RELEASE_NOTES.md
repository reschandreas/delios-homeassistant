# v0.1.0

First public release of the Delios Home Assistant custom integration.

## Features

- Config flow in the UI. Enter the inverter host and credentials. The flow validates them on setup.
- Local polling of the device REST API. Default 30 seconds, configurable.
- Sensors:
  - Live values: PV power, two string voltages and currents, battery state of charge, battery power, voltage and current, grid power, voltage and current, house power, self-consumption percent, grid share percent.
  - Lifetime energy: PV, bought, injected, self-consumed (kWh).
  - Firmware: machine, AC inverter, PV inverter, battery inverter, web.
  - System: WiFi, LAN, USB.
  - Last alarm code, plus the recent alarm list.
- Binary sensors: inverter, PV, battery, DDI and Li alarms, plus Li warning.
- One device named "Delios Inverter", with manufacturer and model.
- Brand icon and logo included.

## Installation

HACS (recommended): add `https://github.com/reschandreas/delios-homeassistant` as a custom repository (category Integration), install, restart, then add via UI.

Manual: copy `custom_components/delios` into `config/custom_components/`, restart, add via UI.

## Configuration

- Host: the inverter IP or hostname.
- Username and password: factory defaults are `user/user`, `installer/installer`, `service/service`. Use `service` for full access.

## Security notes

- The device ships with default credentials and no forced change. Change the password after pairing.
- Polling is read-only. The integration does not change inverter settings.

## Compatibility

Home Assistant Core 2024.x or newer (tested on 2026.11.2). Python 3.12 or newer.

## License

MIT

## Acknowledgements

Reverse-engineered from the device's own web interface (Delios Srl hybrid inverter, firmware 1.0.05). Not affiliated with Delios Srl.
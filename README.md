# Delios Home Assistant Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Custom integration for **Delios** hybrid inverters (local polling over the device's REST API).

## Features

- Live dashboard: PV power, string V/I, battery SOC/power/V/I, grid power/V/I, house power, self-consumption %.
- Alarms: binary sensors for Inv/PV/Battery/DDI/Li alarms + warnings, plus a "Last Alarm" sensor with recent codes.
- Lifetime energy totalizers (PV bought/injected/self-consumed).
- Calculated grid-import, grid-export, and PV energy from live power for the Energy dashboard.
- Firmware versions and system status (WiFi/LAN/USB).

## Installation

### HACS (recommended)

1. HACS → Integrations → ⋮ → **Custom repositories**.
2. Add this repository URL, category **Integration**.
3. Find **Delios** → Download → restart Home Assistant.
4. Settings → Devices & Services → **Add Integration** → Delios.

### Manual

1. Copy `custom_components/delios` into your Home Assistant `config/custom_components/`.
2. Restart Home Assistant.
3. Add the integration via UI.

## Configuration

Enter your inverter's host/IP and credentials. Default factory credentials are `user/user`, `installer/installer`, `service/service` (use `service` for full access).

## Options

- Scan interval (seconds, default 30).

## Energy dashboard

The integration calculates these energy sensors from live power using trapezoidal Riemann integration:

- **Delios Grid Import Energy**
- **Delios Grid Export Energy**
- **Delios Calculated PV Energy**

They start at zero, retain their totals across Home Assistant restarts, and do not include historical energy or energy used while Home Assistant was offline. No template or Riemann-sum helpers are required.

After deploying and restarting, confirm the sensors have numeric states. Then open **Settings → Dashboards → Energy** and select them for grid import/export and solar production. Remove existing alperia sources only after the Delios sources are working. Existing lifetime totalizers and their long-term statistics are left unchanged.

## Standalone client

```bash
python delios_client.py --host http://<device-host> --user service --password service
```

## Security

The device ships with default credentials and no forced change. After pairing, change the password via the device UI or `PUT /api/v1/user/password` so anyone on your LAN cannot read your inverter data.

## Development

See `API.md` for the reverse-engineered API reference.

## License

MIT
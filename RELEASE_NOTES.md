# v0.1.0 — Initial release

First public release of the **Delios** Home Assistant custom integration.

## ✨ Features

- **Config flow** (UI): enter inverter host + credentials, validated on setup.
- **Local polling** (default 30s, configurable) of the device's REST API.
- **Sensors**:
  - Live: PV power, PV string V/I (×2), battery SOC/power/V/I, grid power/V/I, house power, self-consumption %, grid share %.
  - Lifetime energy totalizers: PV, bought, injected, self-consumed (kWh).
  - Firmware versions: machine, AC inverter, PV inverter, battery inverter, web.
  - System status: WiFi, LAN, USB.
  - Last alarm code + recent alarm list.
- **Binary sensors**: inverter, PV, battery, DDI, Li alarms + Li warning.
- Grouped under a single "Delios Inverter" device with manufacturer/model info.
- Brand icon and logo included.

## 📦 Installation

### HACS (recommended)
1. HACS → Integrations → ⋮ → Custom repositories.
2. Add `https://github.com/reschandreas/delios-homeassistant`, category **Integration**.
3. Install **Delios** → restart Home Assistant.
4. Settings → Devices & Services → Add Integration → Delios.

### Manual
Copy `custom_components/delios` into `config/custom_components/`, restart, add via UI.

## ⚙️ Configuration
- **Host**: your inverter's IP or hostname.
- **Username / Password**: default factory credentials are `user/user`, `installer/installer`, `service/service`. Use `service` for full access.

## 🔒 Security notes
- The device ships with default credentials and no forced change. Change the password after pairing (via the device UI or `PUT /api/v1/user/password`).
- Polling is read-only; the integration does not modify inverter settings.

## 🛠️ Compatibility
- Home Assistant Core 2024.x+ (tested on 2026.11.2).
- Python 3.12+.

## 📄 License
MIT

## 🙏 Acknowledgements
Reverse-engineered from the device's own web interface (Delios Srl hybrid inverter, firmware 1.0.05). Not affiliated with Delios Srl.
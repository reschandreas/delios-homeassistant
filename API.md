# Delios Inverter Web API — Reverse Engineered

Target device: Delios Srl hybrid inverter (firmware `1.0.05`).
Transport: HTTP or HTTPS on port 80/443 (lighttpd 1.4.31), plus SSH on 22 (Dropbear).
Base URL: `http://<device-host>/api/v1/`

## Authentication

Login is HTTP Basic Auth against `/api/v1/token`:

```
GET/POST /api/v1/token
Authorization: Basic base64(username:password)
```

Response:

```json
{
  "api_key": "<JWT>",
  "expire":  <unix timestamp>,
  "level":   "0|1|2",
  "username": "..."
}
```

The `api_key` is a JWT used as `x-access-token` header on every subsequent call.
Tokens expire after ~365 days (`duration: 31536000`).

Default factory credentials (3 privilege levels):

| username   | password   | level | meaning   |
|------------|------------|-------|-----------|
| `user`     | `user`     | 0     | USER      |
| `installer`| `installer`| 1     | INSTALLER |
| `service`  | `service`  | 2     | SERVICE   |

Refresh an existing token:

```
GET /api/v1/token
x-access-token: <api_key>
```

Change password (PUT, requires valid token):

```
PUT /api/v1/user/password
x-access-token: <api_key>
Content-Type: application/json

{"password": "<new password 5-15 chars>"}
```

## Endpoints (all require `x-access-token`)

### Dashboard (live measurements)

```
GET /api/v1/dashboard
```

Returns `variables[]` with `ctrl_name`/`value`. Key variables:

- `PowerPV` — PV power (kW)
- `VS1`, `IS1`, `VS2`, `IS2` — string voltages/currents
- `PercentBattery`, `PowerBatt`, `VBatt`, `IBatt`
- `PowerGrid`, `VL1`, `IL1`
- `PowerHouse`, `PercentGreen`, `PercentViolet`
- `InvFlag`, `InvAlarm`, `PVAlarm`, `BattAlarm`

### Status

```
GET /api/v1/status
```

`variables[]`: `InvFlag`, `InvAlarm`, `DDIAlarm`, `PVAlarm`, `BattAlarm`, `LiAlarm`, `LiWarning`, `LiEvent`.

### Alarms

```
GET /api/v1/alarms
```

Returns `variables[]` (same as status) plus `alarms[]`:

```json
{"timestamp": "1794653861784", "desc": "E021"}
```

`timestamp` is ms since epoch. `desc` is an alarm code (E004, E008, E013, E014, E016, E020, E021, E025, E051, …).

### Info

```
GET /api/v1/info/system      -> {"variables": null}   (not populated)
GET /api/v1/info/totalizer   -> totalizers
GET /api/v1/info/firmware    -> firmware versions
```

Totalizer response:

```json
{"totalizers": {
  "TotalEnergyPV": "51105.7",
  "TotalEnergyBuyed": "17710.4",
  "TotalEnergyInjected": "20096.9",
  "TotalEnergySelfConsumed": "31008.9"
}}
```

Firmware response: `MachineFW`, `INVacFW`, `INVpvFW`, `INVbattFW`, `firmware`.

### System status

```
GET /api/v1/system/status
```

```json
{"usb": false, "wifi": 1, "lan": -1}
```

(wifi: 0/1, lan: -1/1)

### Charts

```
GET /api/v1/chart/{period}/{from_time}/{to_time}
```

- `period`: `0` = daily (hourly buckets), `1` = weekly (daily buckets), `2` = yearly (monthly buckets)
- `from_time`/`to_time`: unix timestamps in **seconds**, adjusted by the client's timezone offset (JS formula: `(date.getTime() - tzOffset*60000)/1000`).

Response:

```json
{"categories": [...], "netSerie": [...], "sunSerie": [...],
 "homeSerie": [...], "battSerie": [...]}
```

Series values are energy in kWh (or W) per bucket; `null`/empty for no data.

## Error handling

- `401` → token invalid/expired; client redirects to login.
- Other non-2xx → logged, callback error invoked.

## Discovery notes

- No OpenAPI/Swagger exposed; endpoints were extracted from the device's own JavaScript (`/js/index.js`, `/js/pages/*.js`).
- The device is an SPA; unknown paths return the index HTML with HTTP 200, so 404s cannot be relied upon for endpoint discovery. Probe by checking for JSON content-type / parseable JSON body.
- Only 9 REST endpoints exist in v1. There is no write endpoint for inverter settings via this API (settings are managed in-browser over a separate mechanism not exposed here).
- SSH (Dropbear) is open; not investigated.
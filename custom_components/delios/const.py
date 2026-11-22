"""Constants for the Delios integration."""
from datetime import timedelta

DOMAIN = "delios"
DEFAULT_NAME = "Delios Inverter"

DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)
DEFAULT_PORT = 80

# Config keys
CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"

# API
API_BASE = "/api/v1"

# Dashboard variable friendly names + units
DASHBOARD_SENSORS = {
    "PowerPV": ("PV Power", "kW", "power", "measurement"),
    "VS1": ("PV String 1 Voltage", "V", "voltage", "measurement"),
    "IS1": ("PV String 1 Current", "A", "current", "measurement"),
    "VS2": ("PV String 2 Voltage", "V", "voltage", "measurement"),
    "IS2": ("PV String 2 Current", "A", "current", "measurement"),
    "PercentBattery": ("Battery SOC", "%", "battery", "measurement"),
    "PowerBatt": ("Battery Power", "kW", "power", "measurement"),
    "VBatt": ("Battery Voltage", "V", "voltage", "measurement"),
    "IBatt": ("Battery Current", "A", "current", "measurement"),
    "PowerGrid": ("Grid Power", "kW", "power", "measurement"),
    "VL1": ("Grid Voltage L1", "V", "voltage", "measurement"),
    "IL1": ("Grid Current L1", "A", "current", "measurement"),
    "PowerHouse": ("House Power", "kW", "power", "measurement"),
    "PercentGreen": ("Self Consumption", "%", None, "measurement"),
    "PercentViolet": ("Grid Share", "%", None, "measurement"),
}

TOTALIZER_SENSORS = {
    "TotalEnergyPV": ("Total PV Energy", "kWh", "energy", "total_increasing"),
    "TotalEnergyBuyed": ("Total Energy Bought", "kWh", "energy", "total_increasing"),
    "TotalEnergyInjected": ("Total Energy Injected", "kWh", "energy", "total_increasing"),
    "TotalEnergySelfConsumed": ("Total Self-Consumed", "kWh", "energy", "total_increasing"),
}

FIRMWARE_SENSORS = {
    "MachineFW": ("Machine Firmware", None, None, None),
    "INVacFW": ("Inverter AC Firmware", None, None, None),
    "INVpvFW": ("Inverter PV Firmware", None, None, None),
    "INVbattFW": ("Inverter Battery Firmware", None, None, None),
    "firmware": ("Web Firmware", None, None, None),
}

SYSTEM_SENSORS = {
    "wifi": ("WiFi Status", None, None, None),
    "lan": ("LAN Status", None, None, None),
    "usb": ("USB Connected", None, None, None),
}

ALARM_BINARY = {
    "InvAlarm": "Inverter Alarm",
    "PVAlarm": "PV Alarm",
    "BattAlarm": "Battery Alarm",
    "DDIAlarm": "DDI Alarm",
    "LiAlarm": "Li Alarm",
    "LiWarning": "Li Warning",
}
"""Sensor platform for Delios."""
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ALARM_BINARY,
    DASHBOARD_SENSORS,
    DOMAIN,
    FIRMWARE_SENSORS,
    SYSTEM_SENSORS,
    TOTALIZER_SENSORS,
)
from .coordinator import DeliosCoordinator
from .energy import DeliosCalculatedEnergySensor

_LOGGER = logging.getLogger(__name__)

DEVICE_CLASS_MAP = {
    "power": SensorDeviceClass.POWER,
    "voltage": SensorDeviceClass.VOLTAGE,
    "current": SensorDeviceClass.CURRENT,
    "battery": SensorDeviceClass.BATTERY,
    "energy": SensorDeviceClass.ENERGY,
}

STATE_CLASS_MAP = {
    "measurement": SensorStateClass.MEASUREMENT,
    "total_increasing": SensorStateClass.TOTAL_INCREASING,
}


def _device_info(coordinator, entry):
    return {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": entry.title or "Delios Inverter",
        "manufacturer": "Delios",
        "model": "Hybrid Inverter",
    }


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: DeliosCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}
    entities = []

    # Dashboard sensors
    dash_vars = {
        v["ctrl_name"]: v["value"]
        for v in (data.get("dashboard", {}).get("variables") or [])
    }
    for key, (name, unit, dev, sc) in DASHBOARD_SENSORS.items():
        if key in dash_vars:
            entities.append(DeliosDashboardSensor(coordinator, entry, key, name, unit, dev, sc))

    # Totalizer sensors
    totals = data.get("totalizer", {}).get("totalizers") or {}
    for key, (name, unit, dev, sc) in TOTALIZER_SENSORS.items():
        if key in totals:
            entities.append(DeliosTotalizerSensor(coordinator, entry, key, name, unit, dev, sc))

    # Calculated energy from live power
    entities.extend(
        [
            DeliosCalculatedEnergySensor(
                coordinator, entry, "PowerGrid", "Grid Import Energy", 1
            ),
            DeliosCalculatedEnergySensor(
                coordinator, entry, "PowerGrid", "Grid Export Energy", -1
            ),
            DeliosCalculatedEnergySensor(
                coordinator, entry, "PowerPV", "Calculated PV Energy", 1
            ),
        ]
    )

    # Firmware sensors
    fw_vars = {
        v["ctrl_name"]: v["value"]
        for v in (data.get("firmware", {}).get("variables") or [])
    }
    for key, (name, unit, dev, sc) in FIRMWARE_SENSORS.items():
        if key in fw_vars:
            entities.append(DeliosFirmwareSensor(coordinator, entry, key, name))

    # System status sensors
    ss = data.get("system_status") or {}
    for key, (name, unit, dev, sc) in SYSTEM_SENSORS.items():
        if key in ss:
            entities.append(DeliosSystemSensor(coordinator, entry, key, name))

    # Last alarm code sensor
    entities.append(DeliosLastAlarmSensor(coordinator, entry))

    async_add_entities(entities)


class _Base(CoordinatorEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self):
        return _device_info(self.coordinator, self._entry)


class DeliosDashboardSensor(_Base, SensorEntity):
    def __init__(self, coordinator, entry, key, name, unit, dev, sc):
        super().__init__(coordinator, entry)
        self._key = key
        self._attr_name = f"Delios {name}"
        self._attr_unique_id = f"{entry.entry_id}_dash_{key}"
        self._unit = unit
        self._dev = dev
        self._sc = sc

    @property
    def native_unit_of_measurement(self):
        return self._unit

    @property
    def device_class(self):
        return DEVICE_CLASS_MAP.get(self._dev)

    @property
    def state_class(self):
        return STATE_CLASS_MAP.get(self._sc)

    @property
    def native_value(self):
        vars_ = {
            v["ctrl_name"]: v["value"]
            for v in ((self.coordinator.data or {}).get("dashboard", {}).get("variables") or [])
        }
        val = vars_.get(self._key)
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return val


class DeliosTotalizerSensor(_Base, SensorEntity):
    def __init__(self, coordinator, entry, key, name, unit, dev, sc):
        super().__init__(coordinator, entry)
        self._key = key
        self._attr_name = f"Delios {name}"
        self._attr_unique_id = f"{entry.entry_id}_tot_{key}"
        self._unit = unit

    @property
    def native_unit_of_measurement(self):
        return self._unit

    @property
    def device_class(self):
        return SensorDeviceClass.ENERGY

    @property
    def state_class(self):
        return SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self):
        totals = (self.coordinator.data or {}).get("totalizer", {}).get("totalizers") or {}
        val = totals.get(self._key)
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return val


class DeliosFirmwareSensor(_Base, SensorEntity):
    def __init__(self, coordinator, entry, key, name):
        super().__init__(coordinator, entry)
        self._key = key
        self._attr_name = f"Delios {name}"
        self._attr_unique_id = f"{entry.entry_id}_fw_{key}"

    @property
    def native_value(self):
        vars_ = {
            v["ctrl_name"]: v["value"]
            for v in ((self.coordinator.data or {}).get("firmware", {}).get("variables") or [])
        }
        return vars_.get(self._key)


class DeliosSystemSensor(_Base, SensorEntity):
    def __init__(self, coordinator, entry, key, name):
        super().__init__(coordinator, entry)
        self._key = key
        self._attr_name = f"Delios {name}"
        self._attr_unique_id = f"{entry.entry_id}_sys_{key}"

    @property
    def native_value(self):
        ss = (self.coordinator.data or {}).get("system_status") or {}
        val = ss.get(self._key)
        if isinstance(val, bool):
            return "on" if val else "off"
        if val == 1:
            return "on"
        if val in (0, -1):
            return "off"
        return val


class DeliosLastAlarmSensor(_Base, SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_name = "Delios Last Alarm"
        self._attr_unique_id = f"{entry.entry_id}_last_alarm"

    @property
    def native_value(self):
        alarms = (self.coordinator.data or {}).get("alarms", {}).get("alarms") or []
        if not alarms:
            return None
        # Device returns alarms newest-first, but sort defensively.
        try:
            alarms = sorted(alarms, key=lambda a: int(a.get("timestamp", 0)), reverse=True)
        except (ValueError, TypeError):
            pass
        return alarms[0].get("desc")

    @property
    def extra_state_attributes(self):
        alarms = (self.coordinator.data or {}).get("alarms", {}).get("alarms") or []
        try:
            alarms = sorted(alarms, key=lambda a: int(a.get("timestamp", 0)), reverse=True)
        except (ValueError, TypeError):
            pass
        return {"recent": alarms[:10]}
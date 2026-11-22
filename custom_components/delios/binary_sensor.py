"""Binary sensor platform for Delios."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ALARM_BINARY, DOMAIN
from .coordinator import DeliosCoordinator


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: DeliosCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [DeliosAlarmBinarySensor(coordinator, entry, key, name) for key, name in ALARM_BINARY.items()]
    async_add_entities(entities)


class DeliosAlarmBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, entry, key, name):
        super().__init__(coordinator)
        self._entry = entry
        self._key = key
        self._attr_name = f"Delios {name}"
        self._attr_unique_id = f"{entry.entry_id}_bin_{key}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title or "Delios Inverter",
            "manufacturer": "Delios",
            "model": "Hybrid Inverter",
        }

    @property
    def is_on(self):
        # status variables
        for src in ("status", "dashboard"):
            data = self.coordinator.data.get(src, {})
            vars_ = {v["ctrl_name"]: v["value"] for v in (data.get("variables") or [])}
            if self._key in vars_:
                try:
                    return int(vars_[self._key]) != 0
                except (ValueError, TypeError):
                    return str(vars_[self._key]).lower() in ("1", "true", "on")
        return None
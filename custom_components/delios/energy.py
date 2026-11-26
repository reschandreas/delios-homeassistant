"""Calculated energy sensors for Delios live power measurements."""
import math
import time

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DeliosCoordinator
from .energy_accumulator import EnergyAccumulator


class DeliosCalculatedEnergySensor(CoordinatorEntity, RestoreSensor):
    """Integrate one directional Delios power value into energy."""

    def __init__(self, coordinator, entry, source_key: str, name: str, direction: int):
        super().__init__(coordinator)
        self._entry = entry
        self._source_key = source_key
        self._direction = direction
        self._accumulator = EnergyAccumulator()
        self._attr_name = f"Delios {name}"
        self._attr_unique_id = (
            f"{entry.entry_id}_calculated_energy_{source_key}_{direction}"
        )
        self._attr_native_value = 0.0

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title or "Delios Inverter",
            "manufacturer": "Delios",
            "model": "Hybrid Inverter",
        }

    @property
    def native_unit_of_measurement(self):
        return "kWh"

    @property
    def device_class(self):
        return SensorDeviceClass.ENERGY

    @property
    def state_class(self):
        return SensorStateClass.TOTAL_INCREASING

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        restored = await self.async_get_last_sensor_data()
        if (
            restored is None
            or restored.native_value is None
            or restored.native_unit_of_measurement != "kWh"
        ):
            return
        try:
            value = float(restored.native_value)
        except (TypeError, ValueError):
            return
        if math.isfinite(value) and value >= 0:
            self._attr_native_value = value

    def _directional_power(self):
        try:
            raw_variables = (
                (self.coordinator.data or {})
                .get("dashboard", {})
                .get("variables")
                or []
            )
            variables = {}
            for variable in raw_variables:
                if not isinstance(variable, dict):
                    return None
                variables[variable["ctrl_name"]] = variable["value"]
            power = float(variables.get(self._source_key))
        except (AttributeError, KeyError, TypeError, ValueError):
            return None
        if not math.isfinite(power):
            return None
        return max(self._direction * power, 0.0)

    def _handle_coordinator_update(self):
        now = time.monotonic()
        if self.coordinator.last_update_success:
            power = self._directional_power()
        else:
            power = None
        self._attr_native_value += self._accumulator.add_sample(power, now)
        super()._handle_coordinator_update()

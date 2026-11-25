"""Regression test for totalizer state creation on HA Core 2026.11+."""
from datetime import UTC, datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPONENT_DIR = ROOT / "custom_components" / "delios"


class SensorDeviceClass:
    POWER = "power"
    VOLTAGE = "voltage"
    CURRENT = "current"
    BATTERY = "battery"
    ENERGY = "energy"


class SensorStateClass:
    MEASUREMENT = "measurement"
    TOTAL = "total"
    TOTAL_INCREASING = "total_increasing"


class SensorEntity:
    """Model HA's state-attribute validation for this integration boundary."""

    @property
    def last_reset(self):
        return getattr(self, "_attr_last_reset", None)

    @property
    def state_attributes(self):
        # Mirrors homeassistant/components/sensor/entity.py in HA Core 2026.11.2:
        # last_reset is supported only when state_class is TOTAL.
        if self.last_reset:
            if self.state_class != SensorStateClass.TOTAL:
                raise ValueError(
                    "Setting last_reset for entities with state_class "
                    "other than 'total' is not supported."
                )
            return {"last_reset": self.last_reset.isoformat()}
        return None


class CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator


def _module(name, **attributes):
    module = ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def _load_sensor_module():
    for package in (
        "homeassistant",
        "homeassistant.components",
        "homeassistant.helpers",
        "homeassistant.util",
        "custom_components",
    ):
        module = _module(package)
        module.__path__ = []
        sys.modules[package] = module

    sys.modules["homeassistant.components.sensor"] = _module(
        "homeassistant.components.sensor",
        SensorDeviceClass=SensorDeviceClass,
        SensorEntity=SensorEntity,
        SensorStateClass=SensorStateClass,
    )
    sys.modules["homeassistant.helpers.update_coordinator"] = _module(
        "homeassistant.helpers.update_coordinator",
        CoordinatorEntity=CoordinatorEntity,
    )
    dt_module = _module(
        "homeassistant.util.dt", utcnow=lambda: datetime.now(UTC)
    )
    sys.modules["homeassistant.util.dt"] = dt_module
    sys.modules["homeassistant.util"].dt = dt_module

    package = _module("custom_components.delios")
    package.__path__ = [str(COMPONENT_DIR)]
    sys.modules["custom_components.delios"] = package
    sys.modules["custom_components.delios.coordinator"] = _module(
        "custom_components.delios.coordinator", DeliosCoordinator=object
    )

    name = "custom_components.delios.sensor"
    spec = spec_from_file_location(name, COMPONENT_DIR / "sensor.py")
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sensor_module = _load_sensor_module()


class TotalizerSensorTest(unittest.TestCase):
    def test_total_increasing_sensor_does_not_set_last_reset(self):
        """Re-adding last_reset makes HA reject the entity's state attributes."""
        coordinator = SimpleNamespace(
            data={
                "totalizer": {
                    "totalizers": {"TotalEnergyBuyed": "17710.4"}
                }
            }
        )
        entry = SimpleNamespace(entry_id="test-entry", title="pv")
        sensor = sensor_module.DeliosTotalizerSensor(
            coordinator,
            entry,
            "TotalEnergyBuyed",
            "Total Energy Bought",
            "kWh",
            "energy",
            "total_increasing",
        )

        self.assertEqual(sensor.native_value, 17710.4)
        self.assertIsNone(sensor.state_attributes)


if __name__ == "__main__":
    unittest.main()

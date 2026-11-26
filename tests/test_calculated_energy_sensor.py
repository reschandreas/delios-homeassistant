"""Tests for Delios calculated energy entities."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


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
    @property
    def name(self):
        return getattr(self, "_attr_name", None)

    @property
    def unique_id(self):
        return getattr(self, "_attr_unique_id", None)

    @property
    def native_value(self):
        return getattr(self, "_attr_native_value", None)

    @property
    def last_reset(self):
        return getattr(self, "_attr_last_reset", None)

    @property
    def state_attributes(self):
        if self.last_reset and self.state_class != SensorStateClass.TOTAL:
            raise ValueError("last_reset requires state_class total")
        return None


class RestoreSensor(SensorEntity):
    async def async_get_last_sensor_data(self):
        return getattr(self, "_restored_data", None)


class CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator

    async def async_added_to_hass(self):
        return None

    def _handle_coordinator_update(self):
        return None


def _module(name, **attributes):
    module = ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def _install_stubs():
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
        RestoreSensor=RestoreSensor,
    )
    sys.modules["homeassistant.helpers.update_coordinator"] = _module(
        "homeassistant.helpers.update_coordinator",
        CoordinatorEntity=CoordinatorEntity,
    )
    sys.modules["homeassistant.util.dt"] = _module("homeassistant.util.dt")
    sys.modules["homeassistant.util"].dt = sys.modules["homeassistant.util.dt"]

    package = _module("custom_components.delios")
    package.__path__ = [str(COMPONENT_DIR)]
    sys.modules["custom_components.delios"] = package
    sys.modules["custom_components.delios.coordinator"] = _module(
        "custom_components.delios.coordinator", DeliosCoordinator=object
    )


def _load_integration_module(name):
    full_name = f"custom_components.delios.{name}"
    spec = spec_from_file_location(full_name, COMPONENT_DIR / f"{name}.py")
    module = module_from_spec(spec)
    sys.modules[full_name] = module
    spec.loader.exec_module(module)
    return module


_install_stubs()
energy_module = _load_integration_module("energy")
sensor_module = _load_integration_module("sensor")


def _coordinator(power_grid=2.0, power_pv=2.0):
    variables = []
    if power_grid is not None:
        variables.append({"ctrl_name": "PowerGrid", "value": power_grid})
    if power_pv is not None:
        variables.append({"ctrl_name": "PowerPV", "value": power_pv})
    return SimpleNamespace(
        data={"dashboard": {"variables": variables}},
        last_update_success=True,
    )


def _sensor(coordinator, source_key="PowerGrid", name="Grid Import Energy", direction=1):
    entry = SimpleNamespace(entry_id="test-entry", title="pv")
    return energy_module.DeliosCalculatedEnergySensor(
        coordinator, entry, source_key, name, direction
    )


def _update(sensor, timestamp):
    with patch.object(energy_module.time, "monotonic", return_value=timestamp):
        sensor._handle_coordinator_update()


class CalculatedEnergySensorTest(unittest.IsolatedAsyncioTestCase):
    def test_grid_direction_split(self):
        coordinator = _coordinator(power_grid=-2.0, power_pv=2.0)
        import_sensor = _sensor(coordinator, direction=1)
        export_sensor = _sensor(coordinator, name="Grid Export Energy", direction=-1)
        pv_sensor = _sensor(coordinator, source_key="PowerPV", name="Calculated PV Energy")

        for sensor in (import_sensor, export_sensor, pv_sensor):
            _update(sensor, 100.0)

        coordinator.data = _coordinator(power_grid=-4.0, power_pv=2.0).data
        for sensor in (import_sensor, export_sensor, pv_sensor):
            _update(sensor, 190.0)

        self.assertEqual(import_sensor.native_value, 0.0)
        self.assertAlmostEqual(export_sensor.native_value, 0.075)
        self.assertAlmostEqual(pv_sensor.native_value, 0.05)

    def test_negative_pv_is_clamped_to_zero(self):
        coordinator = _coordinator(power_pv=-2.0)
        sensor = _sensor(coordinator, source_key="PowerPV", name="Calculated PV Energy")

        _update(sensor, 100.0)
        coordinator.data = _coordinator(power_pv=-4.0).data
        _update(sensor, 190.0)
        coordinator.data = _coordinator(power_pv=-1.0).data
        _update(sensor, 200.0)

        self.assertEqual(sensor.native_value, 0.0)

    def test_missing_and_invalid_samples_reset_baseline(self):
        for invalid in (None, "bad", float("nan"), float("inf")):
            with self.subTest(invalid=invalid):
                coordinator = _coordinator(power_grid=2.0)
                sensor = _sensor(coordinator)
                _update(sensor, 100.0)

                coordinator.data = _coordinator(power_grid=invalid).data
                _update(sensor, 110.0)
                self.assertEqual(sensor.native_value, 0.0)

                coordinator.data = _coordinator(power_grid=4.0).data
                _update(sensor, 120.0)
                self.assertEqual(sensor.native_value, 0.0)
                _update(sensor, 210.0)
                self.assertAlmostEqual(sensor.native_value, 0.1)

    def test_malformed_dashboard_structures_reset_baseline(self):
        malformed_payloads = (
            [],
            {"dashboard": []},
            {"dashboard": {"variables": 42}},
            {"dashboard": {"variables": [None]}},
        )
        for payload in malformed_payloads:
            with self.subTest(payload=payload):
                coordinator = _coordinator(power_grid=2.0)
                sensor = _sensor(coordinator)
                _update(sensor, 100.0)

                coordinator.data = payload
                _update(sensor, 110.0)
                self.assertEqual(sensor.native_value, 0.0)

                coordinator.data = _coordinator(power_grid=4.0).data
                _update(sensor, 120.0)
                self.assertEqual(sensor.native_value, 0.0)
                _update(sensor, 210.0)
                self.assertAlmostEqual(sensor.native_value, 0.1)

    def test_failed_coordinator_update_skips_accumulation(self):
        coordinator = _coordinator(power_grid=2.0)
        sensor = _sensor(coordinator)
        _update(sensor, 100.0)

        coordinator.data = _coordinator(power_grid=4.0).data
        coordinator.last_update_success = False
        _update(sensor, 190.0)
        self.assertEqual(sensor.native_value, 0.0)

        coordinator.last_update_success = True
        _update(sensor, 200.0)
        self.assertEqual(sensor.native_value, 0.0)
        _update(sensor, 290.0)
        self.assertAlmostEqual(sensor.native_value, 0.1)

    async def test_restore_does_not_integrate_offline_time(self):
        coordinator = _coordinator(power_pv=2.0)
        sensor = _sensor(coordinator, source_key="PowerPV", name="Calculated PV Energy")
        sensor._restored_data = SimpleNamespace(
            native_value=12.5, native_unit_of_measurement="kWh"
        )

        await sensor.async_added_to_hass()
        _update(sensor, 100.0)
        self.assertEqual(sensor.native_value, 12.5)
        _update(sensor, 190.0)
        self.assertAlmostEqual(sensor.native_value, 12.55)

    async def test_invalid_restored_totals_are_ignored(self):
        invalid_values = ("bad", float("nan"), float("inf"), -1.0)
        for value in invalid_values:
            with self.subTest(value=value):
                coordinator = _coordinator()
                sensor = _sensor(coordinator)
                sensor._restored_data = SimpleNamespace(
                    native_value=value, native_unit_of_measurement="kWh"
                )

                await sensor.async_added_to_hass()
                self.assertEqual(sensor.native_value, 0.0)
                _update(sensor, 100.0)
                self.assertEqual(sensor.native_value, 0.0)

        coordinator = _coordinator()
        sensor = _sensor(coordinator)
        sensor._restored_data = SimpleNamespace(
            native_value=12.5, native_unit_of_measurement="Wh"
        )
        await sensor.async_added_to_hass()
        self.assertEqual(sensor.native_value, 0.0)

    def test_calculated_sensors_have_energy_metadata(self):
        coordinator = _coordinator()
        sensors = (
            _sensor(coordinator),
            _sensor(coordinator, name="Grid Export Energy", direction=-1),
            _sensor(coordinator, source_key="PowerPV", name="Calculated PV Energy"),
        )

        for sensor in sensors:
            self.assertEqual(sensor.device_class, SensorDeviceClass.ENERGY)
            self.assertEqual(sensor.state_class, SensorStateClass.TOTAL_INCREASING)
            self.assertEqual(sensor.native_unit_of_measurement, "kWh")
            self.assertIsNone(sensor.last_reset)
        self.assertEqual(len({sensor.unique_id for sensor in sensors}), 3)

    async def test_sensor_setup_adds_three_calculated_entities(self):
        coordinator = _coordinator()
        coordinator.data.update(
            {
                "totalizer": {"totalizers": {}},
                "firmware": {"variables": []},
                "system_status": {},
                "alarms": {"alarms": []},
            }
        )
        entry = SimpleNamespace(entry_id="test-entry", title="pv")
        hass = SimpleNamespace(data={"delios": {entry.entry_id: coordinator}})
        entities = []

        await sensor_module.async_setup_entry(hass, entry, entities.extend)

        names = {entity.name for entity in entities}
        self.assertIn("Delios Grid Import Energy", names)
        self.assertIn("Delios Grid Export Energy", names)
        self.assertIn("Delios Calculated PV Energy", names)


if __name__ == "__main__":
    unittest.main()

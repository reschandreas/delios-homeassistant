"""Tests for the pure power-to-energy accumulator."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "delios"
    / "energy_accumulator.py"
)
SPEC = spec_from_file_location("delios_energy_accumulator", MODULE_PATH)
energy_accumulator = module_from_spec(SPEC)
SPEC.loader.exec_module(energy_accumulator)
EnergyAccumulator = energy_accumulator.EnergyAccumulator


class EnergyAccumulatorTest(unittest.TestCase):
    def test_trapezoidal_energy_delta(self):
        accumulator = EnergyAccumulator()

        self.assertEqual(accumulator.add_sample(2.0, 100.0), 0.0)
        self.assertAlmostEqual(accumulator.add_sample(4.0, 190.0), 0.075)

    def test_missing_sample_resets_baseline(self):
        accumulator = EnergyAccumulator()
        accumulator.add_sample(2.0, 100.0)

        self.assertEqual(accumulator.add_sample(None, 110.0), 0.0)
        self.assertEqual(accumulator.add_sample(4.0, 120.0), 0.0)

    def test_backward_clock_does_not_accumulate(self):
        accumulator = EnergyAccumulator()
        total = accumulator.add_sample(2.0, 100.0)

        total += accumulator.add_sample(4.0, 90.0)

        self.assertEqual(total, 0.0)

    def test_non_finite_sample_resets_baseline(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                accumulator = EnergyAccumulator()
                accumulator.add_sample(2.0, 100.0)

                self.assertEqual(accumulator.add_sample(value, 110.0), 0.0)
                self.assertEqual(accumulator.add_sample(4.0, 120.0), 0.0)


if __name__ == "__main__":
    unittest.main()

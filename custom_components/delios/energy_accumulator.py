"""Pure power-to-energy accumulation for Delios sensors."""
import math


class EnergyAccumulator:
    """Calculate trapezoidal Riemann energy deltas from power samples."""

    def __init__(self):
        self._previous_power = None
        self._previous_time = None

    def add_sample(self, power_kw: float | None, monotonic_s: float) -> float:
        """Return the energy delta in kWh and update the sample baseline."""
        if power_kw is None or not math.isfinite(power_kw):
            self._previous_power = None
            self._previous_time = None
            return 0.0

        delta = 0.0
        if self._previous_power is not None:
            elapsed = monotonic_s - self._previous_time
            if elapsed > 0:
                average_power = (self._previous_power + power_kw) / 2
                delta = average_power * elapsed / 3600

        self._previous_power = power_kw
        self._previous_time = monotonic_s
        return delta

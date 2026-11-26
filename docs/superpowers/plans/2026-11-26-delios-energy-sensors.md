# Delios Calculated Energy Sensors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add integration-owned grid-import, grid-export, and PV energy sensors calculated from live Delios power values.

**Architecture:** A pure Python accumulator handles trapezoidal Riemann integration and sample baselines. A thin `RestoreSensor` wrapper reads coordinator values, applies the import/export split, delegates accumulation, and restores totals without integrating offline time. The existing sensor setup creates all three calculated sensors.

**Tech Stack:** Python 3.12+, Home Assistant 2026.11.2, `CoordinatorEntity`, `RestoreSensor`, stdlib `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-26-delios-energy-sensors-design.md`

## Global Constraints

- Target Home Assistant 2026.11.2.
- Calculated sensors use `device_class: energy`, `state_class: total_increasing`, and `kWh`; never set `last_reset`.
- Existing lifetime totalizers and their historical statistics remain unchanged.
- Missing, invalid, non-finite, or failed-update samples do not accumulate energy and reset the baseline.
- Restored totals do not include the offline interval.
- Do not automatically modify Energy dashboard configuration or alperia sources.
- Do not perform git commits or other git mutations unless the user explicitly asks.

## Review Focus

- A failed coordinator poll must not integrate stale power: Task 2 adds `test_failed_coordinator_update_skips_accumulation`.
- A backward clock reading must never reduce the total: Task 1 adds `test_backward_clock_does_not_accumulate`.
- Missing and malformed source data must reset the baseline: Task 2 adds `test_missing_and_invalid_samples_reset_baseline`.
- Positive and negative grid power must feed only the correct direction: Task 2 adds `test_grid_direction_split`.
- Restart restoration must not integrate the offline interval: Task 2 adds `test_restore_does_not_integrate_offline_time`.

---

### Task 1: Pure Riemann accumulator

**Files:**
- Create: `custom_components/delios/energy_accumulator.py`
- Test: `tests/test_energy_accumulator.py`

**Interfaces:**
- Consumes: Power samples in kW and timestamps from a monotonic clock in seconds.
- Produces: `EnergyAccumulator.add_sample(power_kw: float | None, monotonic_s: float) -> float`, returning only the new energy delta in kWh.

- [ ] **Step 1: Write failing accumulator tests**

Create tests with these literal expectations:

```python
accumulator.add_sample(2.0, 100.0) == 0.0
accumulator.add_sample(4.0, 190.0) == 0.075  # avg 3 kW for 90 seconds
```

Also cover:
- `test_missing_sample_resets_baseline`: a `None` sample returns `0.0`, and the following valid sample returns `0.0`.
- `test_backward_clock_does_not_accumulate`: a later sample with an earlier timestamp returns `0.0` and cannot make the total negative.
- `test_non_finite_sample_resets_baseline`: `nan` and infinite inputs return `0.0` and reset the baseline.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest discover -s tests -p 'test_energy_accumulator.py' -v`
Expected: import failure because `energy_accumulator.py` does not exist.

- [ ] **Step 3: Implement `EnergyAccumulator`**

Implement only baseline tracking, finite-value validation, trapezoidal delta calculation, and non-positive elapsed-time handling in `custom_components/delios/energy_accumulator.py`. Do not store an HA total or depend on Home Assistant.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest discover -s tests -p 'test_energy_accumulator.py' -v`
Expected: all accumulator tests pass.

### Task 2: Home Assistant calculated energy entities

**Files:**
- Create: `custom_components/delios/energy.py`
- Modify: `custom_components/delios/sensor.py:47-85`
- Test: `tests/test_calculated_energy_sensor.py`

**Interfaces:**
- Consumes: `EnergyAccumulator.add_sample()` from Task 1 and `coordinator.data["dashboard"]["variables"]`.
- Produces: `DeliosCalculatedEnergySensor(coordinator, entry, source_key: str, name: str, direction: int)` and three entities named `Delios Grid Import Energy`, `Delios Grid Export Energy`, and `Delios Calculated PV Energy`.

- [ ] **Step 1: Write failing entity tests**

Use the real entity and accumulator with lightweight HA stubs, consistent with `tests/test_totalizer_sensor.py`. Control monotonic time and coordinator data; assert observable energy totals, not mock calls.

Cover:
- `test_grid_direction_split`: at 100 s, establish baselines with `PowerGrid=-2.0` and `PowerPV=2.0`; at 190 s with `PowerGrid=-4.0` and `PowerPV=2.0`, export gains `0.075` kWh, import gains `0.0`, and PV gains `0.05` kWh.
- `test_negative_pv_is_clamped_to_zero`: negative PV samples never add energy or create a negative baseline.
- `test_missing_and_invalid_samples_reset_baseline`: missing values, non-numeric strings, and non-finite values leave totals unchanged and prevent accumulation on the next valid sample.
- `test_failed_coordinator_update_skips_accumulation`: `last_update_success=False` leaves the total unchanged and resets the baseline.
- `test_restore_does_not_integrate_offline_time`: restored `12.5` kWh remains `12.5` on the first new sample; accumulation starts only with the following sample.
- `test_calculated_sensors_have_energy_metadata`: all three use `energy`, `total_increasing`, `kWh`, unique IDs, and no `last_reset` attribute.
- `test_sensor_setup_adds_three_calculated_entities`: setup adds the three exact friendly names alongside existing sensors.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest discover -s tests -p 'test_calculated_energy_sensor.py' -v`
Expected: import failure because `energy.py` does not exist.

- [ ] **Step 3: Implement the calculated entity and setup registration**

In `energy.py`, read the named dashboard variable, convert it to a finite float, apply `max(direction * power_kw, 0.0)`, and delegate each valid sample to `EnergyAccumulator`. Add the returned delta to the restored/native total. Use `time.monotonic()` for elapsed time. On restore, set only the saved total and leave the accumulator without a baseline.

In `sensor.py`, instantiate:
- source `PowerGrid`, name `Grid Import Energy`, direction `1`
- source `PowerGrid`, name `Grid Export Energy`, direction `-1`
- source `PowerPV`, name `Calculated PV Energy`, direction `1`

- [ ] **Step 4: Run entity tests to verify they pass**

Run: `python3 -m unittest discover -s tests -p 'test_calculated_energy_sensor.py' -v`
Expected: all calculated-entity tests pass.

- [ ] **Step 5: Prove the regression test remains load-bearing**

Run the existing totalizer regression test, then temporarily restore the fixed totalizer behavior only if needed for the red-green check; do not alter the new energy implementation to make tests pass.

Run: `python3 tests/test_totalizer_sensor.py`
Expected: PASS for the corrected `total_increasing` behavior.

### Task 3: Documentation and complete verification

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-11-26-delios-energy-sensors-design.md`

**Interfaces:**
- Consumes: The three entity names from Task 2.
- Produces: User-facing setup instructions matching the implemented names.

- [ ] **Step 1: Document the Energy dashboard setup**

Explain that calculated sensors start at zero, retain totals across restarts, and do not include historical energy. Instruct the user to select them manually for grid import/export and solar, and to remove alperia only after confirming the new sources work.

- [ ] **Step 2: Run the complete test and syntax suite**

Run:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile custom_components/delios/*.py tests/*.py
git diff --check
```

Expected: all tests pass, compilation exits zero, and `git diff --check` reports no errors.

- [ ] **Step 3: Record deployment-only verification**

In the design document, add an unchecked deployment checklist for: numeric calculated states, increasing import energy during measured grid import, increasing export energy during measured export, and Energy dashboard source selection. Do not claim these live checks until the user deploys and confirms them.

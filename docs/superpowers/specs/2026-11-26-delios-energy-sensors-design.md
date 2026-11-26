# Delios calculated energy sensors

## Intent

Provide reliable grid-import, grid-export, and PV energy sensors for the Home Assistant Energy dashboard. The inverter's live power values update, while its `/api/v1/info/totalizer` values were observed unchanged for ten minutes, including across an hourly boundary.

## Goals

- Calculate kWh inside the Delios integration from existing live kW values.
- Avoid manual template and Riemann-sum helper setup in Home Assistant.
- Preserve calculated totals across Home Assistant restarts.
- Skip accumulation while source data is missing or invalid.
- Keep the existing lifetime totalizer sensors and their historical statistics unchanged.

## Non-goals

- Do not modify the inverter's totalizer behavior.
- Do not change the existing totalizer `state_class` or add `last_reset`.
- Do not delete or migrate historical statistics.
- Do not automatically rewrite the user's Energy dashboard configuration.
- Do not remove the alperia sources automatically.

## Constraints

- Home Assistant 2026.11.2 is the target runtime.
- `PowerGrid` is positive during measured import periods. Chart data suggests it is negative during export; the implementation will define export as the negative portion and tests will make that behavior explicit.
- `PowerPV` is expected to be non-negative; negative or invalid values are treated as zero for accumulation.
- Energy dashboard source selection remains a one-time manual step after deployment.

## Approaches considered

1. **Standard Home Assistant template and Riemann helpers.** No additional custom code, but requires several manual helper entities. Initially selected before the user asked whether the integration could perform the calculation.
2. **Calculated energy sensors inside Delios (selected).** Adds three integration-owned energy sensors and tests, but removes all template and Riemann-helper setup.
3. **Continue using inverter lifetime totalizers.** Rejected because the API counters were observed stale while live power changed.

## Approved design

Add these sensors:

- `Delios Grid Import Energy`: integrate `max(PowerGrid, 0)`.
- `Delios Grid Export Energy`: integrate `max(-PowerGrid, 0)`.
- `Delios Calculated PV Energy`: integrate `max(PowerPV, 0)`.

Use trapezoidal Riemann integration between successful coordinator updates. Each sensor uses `device_class: energy`, `state_class: total_increasing`, and `kWh`. Restore the accumulated total after restart, but do not integrate the offline interval. Missing or invalid source values produce no accumulation and reset the integration baseline.

Add focused tests for import, export, PV accumulation, missing data, invalid data, and restart restoration. Keep the existing regression test proving that `total_increasing` sensors do not set `last_reset`.

## User steps after implementation

Deploy and restart Home Assistant once. Confirm the calculated sensors report values, then select them as grid import/export and solar sources in the Energy dashboard. Remove the alperia sources only after the Delios sources are working.

## Deployment verification

These checks require the updated integration to be deployed and are not yet claimed:

- [ ] All three calculated sensors have numeric states.
- [ ] Grid Import Energy increases during a measured grid-import period.
- [ ] Grid Export Energy increases during a measured grid-export period.
- [ ] The calculated sensors are selected as the Energy dashboard's grid and solar sources.
- [ ] The alperia sources are removed only after the Delios sources are confirmed working.

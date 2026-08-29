> ⚠️ **SYNTHETIC TEST DATA — not a real SCG document.** Generated for retrieval testing.

# Cement Mix Spec

**Department:** Production
**Scope:** Batching plant floor operations

## Purpose

Defines batching plant procedure for standard OPC (Ordinary Portland Cement)
production runs on Line 2 and Line 3.

## Batching sequence

1. Charge coarse aggregate, then 60% of mix water
2. Add cement and supplementary cementitious material
3. Add remaining water with admixture pre-diluted
4. Wet mix minimum 90 seconds after final water addition

## Equipment tolerances

| Parameter | Target | Tolerance |
|---|---|---|
| Cement weigh hopper | setpoint | ±1.0% |
| Aggregate weigh hopper | setpoint | ±2.0% |
| Water meter | setpoint | ±1.0% |
| Mixer discharge temperature | 28°C | ±4°C |

## Operator checks per shift

- Calibrate load cells at shift start; log to batching sheet
- Verify moisture probe reading against oven-dry sample once per shift
- Reject any batch where wet mix time falls below 90 s

## Escalation

Out-of-tolerance weigh hopper: stop the line, notify shift supervisor,
raise a maintenance ticket before resuming.

> ⚠️ **SYNTHETIC TEST DATA — not a real SCG document.** Generated for retrieval testing.

# Data Pipeline Error Handling

**Department:** Engineering

## Retry policy

Transient failures (network, 5xx, timeout) retry with exponential backoff:
3 attempts, base delay 2 s, jitter enabled. Do not retry 4xx client errors.

## Idempotency

Every pipeline stage must be safe to re-run. Key writes on a deterministic
`run_id + partition_key` so a replay overwrites rather than duplicates.

## Dead letter handling

Records failing after all retries go to the DLQ topic with the original payload
plus `error_type`, `stage`, and `traceback`. DLQ is reviewed daily.

## Common Python exceptions in pipelines

| Exception | Usual cause | Action |
|---|---|---|
| `KeyError` | Upstream schema drift | Validate against schema registry first |
| `pandas.errors.ParserError` | Malformed CSV delimiter | Quarantine file, alert source owner |
| `TimeoutError` | Slow downstream API | Retry with backoff, then DLQ |
| `MemoryError` | Unbounded read | Switch to chunked iteration |

## Alerting

Page on-call only when DLQ depth exceeds 100 records or a stage fails 3
consecutive scheduled runs.

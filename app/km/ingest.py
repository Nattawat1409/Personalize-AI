"""Phase 3 (incremental ingestion) — NOT YET IMPLEMENTED.

`app/km/index.py:build_index()` currently does a one-shot full rebuild from
mock_km/manifest.json every time it's called. This module will replace that
with the real pipeline from docs/PLAN-v2.md §4:

- event-driven ingestion per new/changed document
- a nightly reconciliation sweep, keyed on `content_hash`
- chunk -> embed -> LLM-classify -> extract metadata -> dedup/merge/conflict
  resolution

Do not call anything in this module yet — it is a placeholder marking where
Phase 3 goes, not working code.
"""

"""Phase 2 (cross-encoder reranker) — NOT YET IMPLEMENTED.

`app/km/index.py:query_index()` currently ranks results with a naive
keyword-overlap score. That is not enough to resolve the corpus's deliberate
test cases — two documents sharing a title but differing in content, or a
superseded document that overlaps heavily with its current revision (see
mock_km/README.md). This module will add the real Phase 2 stage from
docs/PLAN-v2.md §3: a cross-encoder that reads (query, chunk text) pairs
together and re-scores the top-20 down to 5, which is what actually
distinguishes near-duplicate content.

Do not call anything in this module yet — it is a placeholder marking where
Phase 2 goes, not working code.
"""

# Mock KM corpus

Synthetic test corpus for the v2 KM index ([../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) §5.1).

> ⚠️ **Every document here is synthetic.** None is a real SCG document. Figures,
> specifications and procedures are invented for retrieval testing and must never
> be treated as authoritative. Each file carries a banner saying so.

13 documents across 7 departments, built to contain the exact failure modes the
architecture is designed to survive.

## Deliberate collisions

**Same filename, different folder, different content** — proves that keying on
filename is broken:

| Filename | `doc_uid` | Department | Content |
|---|---|---|---|
| `cement-mix-spec.md` | `km-1001` | Production | Batching plant procedure, weigh tolerances |
| `cement-mix-spec.md` | `km-1002` | R&D | Low-carbon lab trial formulations |
| `safety-guidelines.md` | `km-1003` | Plant Operations | Kiln heat, PPE, confined space |
| `safety-guidelines.md` | `km-1004` | Laboratory | Acid handling, fume hoods |

**Same title, superseded revision** — proves decay must not hide old versions:

| `doc_uid` | Version | Effective | Status |
|---|---|---|---|
| `km-1005` | 2020-R1 | 2020-03-01 | superseded by `km-1006` |
| `km-1006` | 2024-R3 | 2024-11-01 | current |

The two revisions overlap heavily on purpose — both are mix-ratio tables for the
same grades. Only the numbers differ (w/c caps tightened, fly ash 25% → 35%,
C50 added, hot-weather curing 10 → 14 days). Title and vector similarity cannot
separate them; only content-aware reranking or an explicit version filter can.

## Category spread

`business_logic` 7 · `general` 4 · `python_topic` 2 — enough to test taxonomy
pruning, including two Engineering documents that are genuinely Python content
sitting inside a cement company.

## manifest.json

Regenerate after editing any document:

```bash
uv run python mock_km/build_manifest.py
```

`content_hash` is computed from real file bytes, so editing a file produces a
genuinely different hash — that is what makes the incremental-ingestion test
meaningful. `doc_uid` is assigned once in `build_manifest.py` and never changes.

## Test cases this corpus supports

From [../docs/PLAN-v2.md](../docs/PLAN-v2.md):

| Test | Query | Expected |
|---|---|---|
| §3 duplicate-title | "What are the weigh hopper tolerances?" | `km-1001` (Production), not R&D |
| §3 duplicate-title | "What clinker percentage did LC-14 use?" | `km-1002` (R&D), not Production |
| §3 duplicate-title | "What PPE do I need near the kiln?" | `km-1003`, not the lab one |
| §7 default recency | "concrete mix ratio for C30" | `km-1006` (2024-R3) |
| §7 explicit version | "concrete mix ratio standard **2020**" | `km-1005`, decay bypassed |
| §7 explicit version | "the **old** mix ratio standard" | `km-1005` via `superseded_by` |
| §7 annotation | any query returning `km-1005` | cited **and** marked superseded |
| §3 taxonomy prune | "how do I handle a KeyError in the pipeline?" | `km-1011`, not a cement doc |
| §4 incremental | re-run ingestion unchanged | no-op, hashes match |
| §4 incremental | edit one file, re-run | only that `content_hash` changes |

## Not included

No PDFs, no scanned documents, no tables-as-images. If Cimie's real KM contains
those, extraction quality becomes its own problem and needs separate testing —
this corpus does not cover it.

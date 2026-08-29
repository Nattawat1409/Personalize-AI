# PLAN v2 — Personalize-AI → Cimie

Implementation plan for the architecture in [ARCHITECTURE.md](ARCHITECTURE.md).

`ARCHITECTURE.md` is the source of truth for **what and why**. This document is
the source of truth for **how and in what order**.

> **v1 (POC) is done.** Its plan is preserved in [PLAN.md](PLAN.md) and its flow
> in [design.md](design.md). Do not edit those to describe v2 — they are the
> record of what was built and verified.

---

## 0. What already exists (do not rebuild)

Built, tested, and working — reuse as-is:

| Component | File | Reuse in v2 |
|---|---|---|
| LangGraph pipeline, 9 nodes | `app/graph.py`, `app/nodes/*.py` | Extend, don't replace |
| Personal topic router | `app/nodes/search_TopicIndex.py` | Unchanged |
| 3-genre classifier (rules verbatim) | `app/nodes/decision_worth.py` | Extend to route episodic |
| Atomic file store | `app/memory/store.py` | Extend |
| Terminal chat loop + trace | `app/main.py` | Unchanged |

Two v1 bugs already fixed — do not regress them:
- `assemble_content` needs `defer=True` (LangGraph edges are an **OR-join**; without it the node fires once per predecessor)
- Every no-match branch in `search_TopicIndex` must return `"topic_content": ""` (otherwise a topic matched earlier in the session leaks into later unrelated turns)

---

## 1. Phase order

Follow this order. Each phase is independently shippable and testable.

| Phase | Delivers | Blocked by |
|---|---|---|
| **P1** | KM index separated from personal index | — |
| **P2** | Cross-encoder reranker | P1 |
| **P3** | Incremental ingestion (event + nightly sweep) | P1 |
| **P4** | `doc_id` = content hash + metadata schema | P1 |
| **P5** | Episodic layer + nightly consolidation | — (independent of P1–P4) |
| **P6** | KM staleness decay | P3, P4 |

P1–P2 resolve the stated production concerns. P3–P4 stop them recurring.
P5–P6 raise personalisation quality.

**P5 can be built first if you want a visible win early** — it is the only phase
that touches nothing in the KM path, and it is the one that makes
`Recurring Interests` finally work.

---

## 2. Phase 1 — separate the indexes

### New config

```python
# app/config.py  (additions)
KM_ROOT           = Path("...")          # the KM document folder
KM_INDEX_PATH     = MEMORY_ROOT / "km_index"   # NOT topics_index.json
KM_TOP_K          = 20                   # hybrid retrieve depth
KM_RERANK_K       = 5                    # after rerank
EPISODIC_ROOT     = MEMORY_ROOT / "episodic"
EPISODIC_DAYS     = 7                    # days loaded per turn
```

### Hard rule

`topics_index.json` stays **personal memory only**. Nothing from the KM folder
is ever written into it, and the LLM router is never given KM documents. If a
change would put 1,500 documents in front of the router, that change is wrong.

### New module

`app/km/` — parallel to `app/memory/`, not inside it:

```
app/km/
  __init__.py
  index.py       # build / query the hybrid index
  ingest.py      # chunk, embed, classify, dedup
  rerank.py      # cross-encoder stage
  schema.py      # chunk metadata model
```

### Acceptance for P1

- Personal-memory acceptance tests from `PLAN.md` §11 still pass unchanged
- A KM query returns KM chunks; a personal recall query returns topic `.md`
- `topics_index.json` contains zero KM-derived entries

---

## 3. Phase 2 — reranker

Insert as the final retrieval stage, after taxonomy pruning:

```
query → hybrid retrieve (top-20) → taxonomy prune → rerank (→5) → context
```

Model choice is Open Decision #3 in `ARCHITECTURE.md`. Start with a
cross-encoder (BGE-m3 or Jina-m0); move to an LLM-based reranker only if
measured quality demands it and latency allows.

### Acceptance for P2 — the duplicate-name test

This is the test that matters. Construct it deliberately:

1. Put two KM documents with the **same title** and **different content** in
   different departments (e.g. `Cement Mix Spec` — Production vs R&D)
2. Ask a question answerable only by one of them
3. Assert the correct one ranks first **and** the cited `doc_id` matches
4. Repeat with a superseded version pair (2020 vs 2024 revision) — the current
   one must win

Log the pre-rerank and post-rerank ordering for every query during testing;
this is the only way to see the reranker earning its place.

---

## 4. Phase 3 — incremental ingestion

**Not a node in the chat graph.** A separate process.

| Trigger | Scope | Purpose |
|---|---|---|
| Document created/updated in KM | That document only | Freshness within minutes |
| Nightly sweep | Whole KM folder, hash comparison | Catch missed events |

Never scan all 1,500 documents at session start or per turn.

### Ingestion steps

1. Compute `doc_id = SHA-256(content)`; skip if unchanged
2. Chunk (preserve sentence boundaries)
3. Embed + BM25-index each chunk
4. LLM-classify into the 3-genre taxonomy
5. Extract metadata (§5 below)
6. Dedup / merge / conflict-resolve against existing entries
7. Atomic index write

### Acceptance for P3

- Adding one document re-indexes exactly that document (assert by timing and by
  a counter, not by eye)
- Re-uploading an identical file is a no-op
- Deleting a file removes it from the index on the next sweep
- A document added at 10:00 is retrievable by 10:05 without a restart

---

## 5. Phase 4 — identity and metadata

```python
class KMChunk(BaseModel):
    doc_uid: str           # STABLE document identity — survives edits
    content_hash: str      # sha256 of content — changes on every edit
    chunk_id: str          # f"{doc_uid}#{n:03d}"
    source_path: str
    title: str
    version: str | None
    effective_date: date | None
    department: str | None
    category: Literal["business_logic", "python_topic", "general"]
    superseded_by: str | None = None    # -> doc_uid
    last_accessed: datetime | None = None
    access_count: int = 0
    text: str
```

**Two ids, and they do different jobs.** Hashing content alone is not enough: an
edited document would get a new id, become a "new" document, and silently break
every earlier citation.

| Field | Role |
|---|---|
| `doc_uid` | Identity. Citations, dedup, `superseded_by`. Stable across edits. |
| `content_hash` | Revision fingerprint. Only answers "changed → re-index?" |

`doc_uid` comes from the KM system's own id when one exists; otherwise assign at
first ingest and persist it.

**Filename is never an identifier.** It is display metadata only. Any lookup,
dedup, or citation keyed on filename is a bug.

### Citation returned with an answer

Capped at `SOURCES_TOP_K = 5`, deduped on `doc_uid` (so two revisions of one
document collapse to a single citation, newest winning):

```json
{
  "doc_uid": "km-4471",
  "title": "Cement Mix Spec",
  "version": "2024-R3",
  "source_path": "KM/production/cement-mix-spec.pdf",
  "score": 0.91
}
```

`content_hash` is not included — it names a revision, not a document, and means
nothing to a reader.

**Plumbing already exists in v1.** `State["sources"]`, `create_topic(sources=)`,
`append_topic(sources=)`, `merge_sources()` and `SOURCES_TOP_K` are built and
tested; v1 always passes `[]` because it has no retrieval. v2 fills it from the
rerank stage — no schema migration needed.

---

## 6. Phase 5 — episodic layer

### Files

```
app/memory/episodic/
  YYYY-MM-DD.md     # one per active day
  summary.md        # rolling global summary
```

### Daily log format

```markdown
---
date: 2026-08-29
turn_count: 6
---

### 09:14 — business_logic
**Q:** How is cement produced?
**Gist:** Asked for the production process; wanted the kiln stage explained simply.

### 09:31 — python_topic
**Q:** How do I catch exceptions?
**Gist:** Follow-up on error handling; asked for a code example first.
```

### Graph changes

1. `loading_userProfiles` also loads `summary.md` + last `EPISODIC_DAYS` of logs
2. `decision_worth` gains an episodic write alongside its existing action —
   **this is the one place v2 intentionally departs from the v1 diagram**, whose
   4-way branch is exclusive. Every remembered turn appends to the episodic log
   *in addition to* its topic/profile action. Record the departure; don't
   silently diverge.
3. New node `append_episodic`

### Nightly consolidation job

```
episodic/*.md  →  daily summaries  →  summary.md  →  inferred portrait lines
```

Portrait aggregation writes a `Recurring Interests` line only above the
confidence threshold (default: ≥3 occurrences in 7 days — Open Decision #2).
Lines are tagged `(inferred)`; direct user statements are tagged `(direct)`.

### Acceptance for P5

| Test | Expected |
|---|---|
| Ask 3 topics today, restart, ask *"what did we discuss today?"* | Summarised from `episodic/`, not from the checkpointer |
| Ask about cement on 3 separate days, run nightly job | `Recurring Interests` gains a cement line tagged `(inferred)` |
| Ask about cement once | **No** `Recurring Interests` line — threshold not met |
| User says "I prefer short answers" | Appears immediately, tagged `(direct)` — not waiting for the nightly job |

The third row is the one that catches over-eager inference. Do not skip it.

---

## 7. Phase 6 — KM staleness decay

Nightly job recomputes `freshness_score` per document from `effective_date`,
`last_accessed`, `access_count`. Retrieval applies it **last**, as a multiplier
on the reranked score.

**Three hard constraints:**

1. **Ranking multiplier, never a filter.** Decay may lower a rank. It may never
   remove a document from results or from the index.
2. **Always ranked below relevance.** An old document that matches the question
   exactly must still beat a fresh one that barely matches. Decay breaks
   near-ties only.
3. **KM index only.** Never `user_profile.md`, `episodic/`, or topic `.md`.
   `ARCHITECTURE.md` §7 gives the reasoning: document correctness decays with
   time, identity facts do not, and a profile decay error costs user trust.

### Acceptance for P6 — the explicit-version test

Decay is only safe if asking for an old revision on purpose still works. Test
with a superseded pair (2020 vs 2024) in the index:

| Query | Expected winner | What it proves |
|---|---|---|
| "cement mix ratio" | 2024-R3 | Decay breaks the tie toward current |
| "cement mix ratio **2020**" | **2020** | Query understanding extracted the version into a metadata filter, applied *before* scoring — decay never ran |
| "the **old** cement mix spec" | **2020** | Same path via `superseded_by IS NOT NULL` |

Also assert the superseded document is **annotated, not hidden**: the answer
cites it and notes it was superseded by 2024-R3.

If any row fails, `freshness_score` is being applied as a filter or weighted
above relevance — both are defects, not tuning.

---

## 8. Cross-phase rules

- **Atomic writes everywhere** — temp file → `os.replace()`. The KM index gets
  the same treatment as `topics_index.json`.
- **Trace every stage.** v1's `--- memory ---` block is how the concept is
  demonstrated and debugged. v2 adds: retrieval candidates, pre/post rerank
  order, cited `doc_id`s, and ingestion events.
- **Never let an unvalidated id reach a file path** — applies to the KM index
  exactly as it applies to the router.
- **Async write-back** (Open Decision #5). v1 blocks the user until memory is
  written; with ingestion and reranking added, keeping writes on the critical
  path becomes a real latency problem. Queue per user to avoid a stale read on
  an immediate follow-up.

---

## 9. Definition of done

- [ ] Duplicate-title KM documents resolve to the correct one, cited by `doc_uid`
- [ ] A superseded document loses to its current revision **by default**
- [ ] …but wins when the user asks for it explicitly ("2020", "the old spec")
- [ ] A superseded document is annotated as superseded, never hidden
- [ ] A document added mid-session is retrievable without restart
- [ ] Re-uploading an unchanged document is a no-op
- [ ] `topics_index.json` contains no KM entries
- [ ] `"what did we discuss yesterday?"` answers from `episodic/` after restart
- [ ] `Recurring Interests` populates only above threshold
- [ ] All v1 acceptance tests (`PLAN.md` §11) still pass

# Personalize-AI

A proof of concept for an AI memory system, being built to eventually apply to
**Cimie** — the company's production AI chatbot.

The core idea: the agent files every conversation into the right place on
disk — by topic, by day, and by what it learns about you — so that in a
**later session** it can read those files back and answer in a way that
remembers you, instead of starting from zero every time.

This README is a map of the project by **zone**, matching the architecture
diagram the team has seen in planning. For each zone: what it is, whether
it's built, and how to test it yourself by hand.

---

## Two tracks — read this before touching anything

| | **v1 — POC** | **v2 — Cimie target** |
|---|---|---|
| Status | ✅ Built and passing its acceptance tests | 🚧 In progress — see zone table below |
| Docs | [docs/design.md](docs/design.md), [docs/PLAN.md](docs/PLAN.md) | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/PLAN-v2.md](docs/PLAN-v2.md) |
| Scope | Personal memory only (no company documents) | Personal memory **+** a separate index over company documents (KM) |

If you're not sure which track something belongs to: **v1 is what actually
runs today when you chat with the app.** v2 is being built alongside it,
phase by phase, without breaking v1.

---

## Setup

```bash
uv sync
uv run python -m app.main
```

You'll need a `.env` at the repo root with `LITELLM_URL` and `API_KEY` set —
those are the only two this app actually reads (`example.env` in the repo is
currently empty, don't rely on it). Module form (`-m app.main`) matters — the
package uses relative imports and will error if run as a plain script.

---

## The project by zone

```
┌─────────────────────────────────────────────────────────────────┐
│ ZONE 1 — OFFLINE: KM Ingestion                                  │
├─────────────────────────────────────────────────────────────────┤
│ ZONE 2 — ONLINE: Chat Turn                                       │
│   ┌───────────────────────────┐  ┌───────────────────────────┐ │
│   │ Upper path: System memory │  │ Lower path: Personal memory│ │
│   └───────────────────────────┘  └───────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ ZONE 3 — Write-back                                              │
├─────────────────────────────────────────────────────────────────┤
│ ZONE 4 — NIGHTLY                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Zone 1 — Offline: KM Ingestion

Turning company documents into something searchable. **Runs outside the chat
— never per message.**

| Piece | Status | File |
|---|---|---|
| Separate index from personal memory | ✅ Built (Phase 1) | `app/km/index.py`, `app/km/schema.py` |
| Real chunk/embed/classify/dedup pipeline | ❌ Not built (Phase 3) | `app/km/ingest.py` (stub only) |
| `doc_uid` + `content_hash` schema | ✅ Built, using the mock corpus's manifest | `app/km/schema.py` |
| Event-driven + nightly-sweep updates | ❌ Not built (Phase 3) | — |

**What exists right now:** a mock company-document corpus at
[mock_km/](mock_km/) (13 synthetic documents, deliberately containing
duplicate filenames with different content, and a superseded-document pair —
see [mock_km/README.md](mock_km/README.md)), and a KM index builder/query
function that reads it.

**⚠️ Not wired into the chat yet.** `app/km/index.py` is a standalone module.
Chatting in `app/main.py` never touches it. Test it directly in Python (see
below).

### Zone 2 — Online: Chat Turn

**Upper path — System memory (KM retrieval)**

| Piece | Status |
|---|---|
| Query understanding, metadata filter | ❌ Not built |
| Hybrid retrieve (BM25 + dense) | ❌ Not built — current search is naive keyword overlap, a placeholder |
| Taxonomy prune | ❌ Not built |
| Cross-encoder reranker | ❌ Not built (Phase 2) — this is what will actually resolve same-title-different-content and superseded-document cases |
| Freshness multiplier | ❌ Not built (Phase 6) |

**Lower path — Personal memory**

| Piece | Status | File |
|---|---|---|
| Load `user_profile.md` | ✅ Built (v1) | `app/nodes/loading_userProfiles.py` |
| Load episodic summary + recent days | ✅ Built (Phase 5) | same file |
| LLM router over `topics_index.json` | ✅ Built (v1) | `app/nodes/search_TopicIndex.py` |
| Read matched topic `.md` | ✅ Built (v1) | `app/nodes/specific_topic.py` |
| Assemble context | ✅ Built (v1 + Phase 5) | `app/nodes/assemble_content.py` |
| Generate answer | ✅ Built (v1) | `app/nodes/generate_answer.py` |

This whole path is what runs when you actually chat with `app/main.py` today.

### Zone 3 — Write-back

Deciding whether a turn is worth remembering, and where.

| Piece | Status | File |
|---|---|---|
| Decide skip / append / create / profile | ✅ Built (v1) | `app/nodes/decision_worth.py` |
| Append/create topic `.md` | ✅ Built (v1) | `app/nodes/append_md.py`, `app/nodes/create_md.py` |
| Update `user_profile.md`, tagged `(direct)` | ✅ Built (v1 + Phase 5 tagging) | `app/nodes/update_UserProfile.py` |
| Append to episodic log | ✅ Built (Phase 5) — runs **in addition to** whichever of the above ran, on every non-skip turn | `app/nodes/append_episodic.py` |

**⚠️ Known gap vs. the target design:** this currently runs **synchronously**
— you wait for the write before you see the answer. The target architecture
calls for this to be async (off the critical path). Not yet done.

### Zone 4 — Nightly

Consolidating the day's activity. **A standalone script — not a graph node,
does not run per chat turn.**

| Piece | Status | File |
|---|---|---|
| Daily summary → global summary | ✅ Built (Phase 5) | `app/jobs/nightly_consolidate.py` |
| Aggregate → `user_profile.md` Recurring Interests, tagged `(inferred)` | ✅ Built (Phase 5), with a threshold guard against inferring from a single mention | same file |
| Recompute KM `freshness_score` | ❌ Not built (Phase 6) — needs Zone 1's real ingestion first | — |

Run it by hand:

```bash
uv run python -m app.jobs.nightly_consolidate
```

---

## Manual testing, by zone

### Testing Zone 2 (lower path) + Zone 3 — the part that actually runs today

```bash
uv run python -m app.main
```

Type a question, read the answer, then read the `--- memory ---` block
underneath it — every node appends one line there explaining what it did.
That block is your main debugging tool; read it before assuming something's
broken.

**Things worth trying:**
- Ask about a topic, then a related follow-up — check whether it appended to
  the same file or created a sibling one (`ls app/memory/business_logic/` etc.)
- Say something like *"I prefer short answers"* — check it shows up in
  `app/memory/user_profile.md` tagged `(direct)`, immediately, not after a delay
- **The real test — kill the process and restart it.** Ask *"what have we
  discussed today?"* — it should recall correctly using only what's on disk,
  since the old process's memory is gone. If this works, the core concept is
  proven.
- Say something small-talk-y like *"thanks!"* — check the trace shows
  `action=skip` and no new file was written

### Testing Zone 1 — the KM index (not reachable via chat yet)

```bash
uv run python -c "
from app.km.index import build_index, query_index
print('indexed:', build_index(), 'chunks')
for r in query_index('weigh hopper tolerance cement')[:3]:
    print(r['doc_uid'], r['department'], r['title'])
"
```

Check `mock_km/README.md` for the specific test queries the corpus was built
to support (duplicate titles, a superseded document pair) and what each
should return.

### Testing Zone 4 — the nightly job

```bash
uv run python -m app.jobs.nightly_consolidate
```

Run it after a few days of real chat activity (or after backdating a couple
of `app/memory/episodic/YYYY-MM-DD.md` files for testing — see the file format
in `docs/PLAN-v2.md` §6). Then check:
- `app/memory/episodic/summary.md` — did it pick up new daily digests?
- `app/memory/user_profile.md` — did a `Recurring Interests` line appear,
  tagged `(inferred)`, *only* if the same subject came up on 3+ distinct days?

**The one test that matters most here:** ask about something **once**, run the
job, and confirm **no** Recurring Interests line was added. If one appears
from a single mention, the threshold guard is broken.

---

## Where to go deeper

| Question | Read |
|---|---|
| How does the v1 flow work, node by node? | [docs/design.md](docs/design.md), [docs/PLAN.md](docs/PLAN.md) |
| What's the target v2 architecture and why? | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| What's the build order and acceptance criteria for v2? | [docs/PLAN-v2.md](docs/PLAN-v2.md) |
| What's in the mock company-document corpus? | [mock_km/README.md](mock_km/README.md) |

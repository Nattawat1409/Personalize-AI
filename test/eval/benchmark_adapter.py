"""Personalize adapter — the ONLY file that differs between the two systems.

`run_benchmark.py` replays the frozen conversation through whichever adapter it
is pointed at. This one drives the baseline RAG pipeline PLUS the memory layer;
the baseline's own adapter (AI-KM-Agent_BaseCase/test/eval/benchmark_adapter.py)
drives the same pipeline without memory. Same runner, same evalset, same
contract, so the two result files are directly comparable.

Contract (identical to the baseline's — see docs/HANDOFF_NEW_ARCHITECTURE.md §6)
  answer(question, user_id, session_id) -> dict
  reset_memory(user_id)              called once before the first turn
  end_session(user_id, session_id)   called at each session boundary
  SYSTEM_LABEL, MEMORY_ENABLED, NAMESPACE, GENERATION_MODEL

Kill switch:  MEMORY_ENABLED=false  reproduces the baseline exactly (no memory
read, no write-back, prompt byte-identical). Run that first and confirm
retrieval parity before trusting any memory-on number.

`retrieved_chunk_ids` comes from search_raw() on the RAW question, exactly as in
the baseline adapter. Memory never touches it.

Timing: `latency_ms` covers the answer path only, memory READ included (it is
part of what the user waits for). Write-back is measured separately as
`writeback_ms` so its cost is reported, not hidden.
"""

import asyncio
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from tools.general.build import load_env  # noqa: E402

load_env()

from nodes.general.utils import detect_language  # noqa: E402
from service import memory_service as memory  # noqa: E402
from service.graph_llm import LLM_MODEL, answer_query, build_km_searcher  # noqa: E402

MEMORY_ENABLED = memory.memory_enabled()
# The label names the result file, so a memory-off parity run can never be
# mistaken for (or overwrite the file of) a real memory-on run.
SYSTEM_LABEL = "personalize" if MEMORY_ENABLED else "personalize-memoff"
NAMESPACE = "manufactur-profession"
GENERATION_MODEL = LLM_MODEL


def _warn(msg: str) -> None:
    print(f"   !! {msg}", file=sys.stderr, flush=True)


async def answer(question: str, user_id: str, session_id: str) -> dict:
    language = detect_language(question)
    asked_at = datetime.now(timezone.utc)

    # Chunk identity (not timed — this is measurement, not the product path).
    # RAW question only: memory must not alter what retrieval sees.
    raw = await build_km_searcher(NAMESPACE, language).search_raw(question)

    t0 = time.perf_counter()
    read = memory.MemoryRead()
    if MEMORY_ENABLED:
        read = await asyncio.to_thread(memory.read_memory, user_id, question)
    result = await answer_query(question, NAMESPACE, memory_context=read.block or None)
    latency_ms = int((time.perf_counter() - t0) * 1000)

    write = {"action": None, "trace": [], "error": None}
    writeback_ms = 0
    if MEMORY_ENABLED:
        # Awaited before returning: the next turn (and the next session) must
        # see this turn's memory. Runs for refusals too.
        t1 = time.perf_counter()
        write = await asyncio.to_thread(
            memory.write_back, user_id, question, result["answer"], read
        )
        writeback_ms = int((time.perf_counter() - t1) * 1000)

    logged_at = datetime.now(timezone.utc)
    memory_error = read.error or write["error"]
    if memory_error:
        _warn(f"memory error (turn continues without it): {memory_error}")

    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "language": result["language"],
        "floor_triggered": result["floor_triggered"],
        "top_score": result["top_score"],
        # What actually reached the prompt. A floor refusal makes no LLM call,
        # so nothing was injected even if memory was read.
        "memory_used": [] if result["floor_triggered"] else read.used,
        "latency_ms": latency_ms,
        # answer_query() does not surface usage metadata; null, not a guess.
        "tokens": None,
        "retrieved_chunk_ids": [r["id"] for r in raw],
        # --- extra keys (the runner keeps them; the scorer ignores them) ---
        "writeback_ms": writeback_ms,
        # UTC, the same clock the episodic log uses. The scorer checks "when did we
        # discuss X?" answers against these (asked_at <= log entry <= logged_at).
        "asked_at_utc": asked_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "logged_at_utc": logged_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "memory_action": write["action"],
        "memory_error": memory_error,
    }


async def reset_memory(user_id: str) -> None:
    # Always runs, even with the kill switch off: a benchmark must start from a
    # known-empty state, and reset must leave no state behind.
    await asyncio.to_thread(memory.reset_memory, user_id)


async def end_session(user_id: str, session_id: str) -> None:
    if not MEMORY_ENABLED:
        return
    report = await asyncio.to_thread(memory.end_session, user_id, session_id)
    if report.get("error"):
        _warn(report["error"])

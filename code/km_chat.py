"""Interactive KM chat WITH memory — for trying the memory layer by hand.

Counterpart of the baseline's one-shot code/km_chat.py. Each line you type runs
the same path the benchmark adapter uses:

    read memory -> baseline retrieval + floor -> generate -> write back memory

Usage (from the repo root):
    uv run python code/km_chat.py                     # user "demo"
    uv run python code/km_chat.py --user alice
    uv run python code/km_chat.py --user alice --no-memory   # baseline behaviour

Commands inside the chat:
    /end     end the session now (runs the nightly summarisation on demand)
    /reset   wipe this user's memory
    /mem     show what memory currently holds for this user
    exit     quit

Kill switch: MEMORY_ENABLED=false (or --no-memory) makes this behave exactly
like the baseline. Memory lives in data/memory/users/<user>/ (gitignored).
"""

from tools.general.build import load_env

load_env()

import argparse
import asyncio
import sys

from repository.memory_repository import UserMemory
from service import memory_service as memory
from service.graph_llm import answer_query

NAMESPACE = "manufactur-profession"


async def turn(user_id: str, question: str, use_memory: bool) -> None:
    read = memory.MemoryRead()
    if use_memory:
        read = await asyncio.to_thread(memory.read_memory, user_id, question)
    result = await answer_query(question, NAMESPACE, memory_context=read.block or None)

    print(
        f"\n[language={result['language']}] [top_score={result['top_score']:.4f}] "
        f"[floor_triggered={result['floor_triggered']}]"
    )
    print(f"\n{result['answer']}")
    if result["sources"]:
        print("\nSources:")
        for s in result["sources"]:
            print(f"  [{s['id']}] {s['source']} (score={s['score']:.4f})")

    if use_memory:
        injected = [] if result["floor_triggered"] else read.used
        write = await asyncio.to_thread(memory.write_back, user_id, question, result["answer"], read)
        print(f"\n--- memory --- injected: {injected or 'nothing'} | saved as: {write['action']}")
        for err in filter(None, (read.error, write["error"])):
            print(f"  !! {err}", file=sys.stderr)


def show(user_id: str) -> None:
    mem = UserMemory(user_id)
    if not mem.exists():
        print("(no memory stored for this user)")
        return
    print(mem.load_profile())
    for t in mem.load_index()["topics"]:
        print(f"  topic [{t['category']}] {t['id']}: {t['one_liner']}")
    ctx, _ = mem.load_episodic_context()
    print(ctx or "(no episodic log yet)")


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="demo")
    ap.add_argument("--no-memory", action="store_true")
    args = ap.parse_args()
    use_memory = memory.memory_enabled() and not args.no_memory

    print(f"user={args.user} memory={'on' if use_memory else 'off'}  (/end /reset /mem exit)")
    while True:
        try:
            line = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.lower() in ("exit", "quit"):
            break
        if line == "/reset":
            memory.reset_memory(args.user)
            print("memory wiped.")
        elif line == "/mem":
            show(args.user)
        elif line == "/end":
            print(memory.end_session(args.user, "manual"))
        else:
            await turn(args.user, line, use_memory)


if __name__ == "__main__":
    asyncio.run(main())

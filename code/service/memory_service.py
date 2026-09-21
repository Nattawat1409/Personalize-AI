"""The memory layer's public surface — the two places it plugs into the baseline.

    question ─► read_memory() ─► [baseline retrieval + floor, UNCHANGED] ─► prompt ─► LLM
                     │                                                                  │
                     └─ build_memory_block() text is appended to the system prompt      ▼
                                                                          write_back() ◄─ answer

Rules this module exists to enforce (docs/HANDOFF_NEW_ARCHITECTURE.md §5):
- Retrieval never sees memory: read_memory() takes the raw question and its
  output is only ever used to extend the system prompt.
- Memory never changes the floor decision: nothing here is consulted before
  the floor check, and write-back runs whether or not the floor fired.
- Kill switch: MEMORY_ENABLED=false makes the adapter skip this module entirely,
  so the prompt is byte-identical to the baseline's.

Failures in the memory layer never crash a turn: they are captured in `error`
so the caller can record them. A silent memory failure would make the memory
system look worse than it is, so callers must surface them.
"""

import os
from dataclasses import dataclass, field

from nodes.memory.append_episodic import append_episodic
from nodes.memory.append_md import append_md
from nodes.memory.create_md import create_md
from nodes.memory.decision_worth import decision_worth
from nodes.memory.loading_userProfiles import loading_userProfiles
from nodes.memory.search_TopicIndex import search_TopicIndex
from nodes.memory.specific_topic import specific_topic
from nodes.memory.update_UserProfile import update_UserProfile
from repository.memory_repository import (
    EMPTY_SECTION,
    UserMemory,
    extract_topic_sections,
    read_profile_section,
)
from service.memory_consolidation import consolidate
from workflow.state import State

_PROFILE_SECTIONS = ("Identity", "Preferences", "Recurring Interests")

# Appended to the baseline SYSTEM_PROMPT (which is locked and never edited).
# It has to say explicitly how memory relates to the baseline's rule 1
# ("answer ONLY from the Context"), otherwise the model would either ignore the
# notes or refuse to answer questions about the conversation itself.
MEMORY_INSTRUCTIONS = """## Memory of this user (notes from earlier conversations — NOT part of the knowledge base)

How to use the notes below:
- Writing style: apply what you know about the user — their background and how they like answers formatted — to HOW you write the answer (vocabulary, level of detail, structure). This never relaxes rules 1-4 above: every factual claim about the knowledge base must still come only from the Context and cite [Document ID: N].
- Questions about the earlier conversation itself (for example "did we discuss X before?" or "what did I tell you about myself?"): answer them from these notes. If the notes do not say, state plainly that you have no record of it. Never guess or invent what the user said or what was discussed. The notes are not knowledge-base facts, so do not cite them with [Document ID: N].
- Do not bring the notes up when the question is not about them."""


def memory_enabled() -> bool:
    """MEMORY_ENABLED env kill switch. Default on; false/0/no/off turns it off."""
    return os.environ.get("MEMORY_ENABLED", "true").strip().lower() not in ("false", "0", "no", "off")


def apply(state: State, update: dict) -> State:
    """Merge one node's returned dict into the state; `trace` lines accumulate."""
    for key, value in update.items():
        if key == "trace":
            state.setdefault("trace", []).extend(value)
        else:
            state[key] = value  # type: ignore[literal-required]
    return state


def _profile_text(profile_md: str) -> str:
    """Profile without frontmatter and without empty placeholder sections."""
    blocks = []
    for name in _PROFILE_SECTIONS:
        body = read_profile_section(profile_md, name)
        if body and body != EMPTY_SECTION:
            blocks.append(f"{name}:\n{body}")
    return "\n\n".join(blocks)


def build_memory_block(state: State) -> tuple[str, list[str]]:
    """Turn the loaded memory into the text appended to the system prompt.

    Pure (no I/O, no LLM). Returns ("", []) when there is nothing to inject, so
    a user with no memory yet gets exactly the baseline prompt.
    """
    parts: list[str] = []
    used: list[str] = []

    profile = _profile_text(state.get("user_profile", ""))
    if profile:
        parts.append(f"### What you know about this user\n{profile}")
        used.append("user_profile.md")

    episodic = (state.get("episodic_context") or "").strip()
    if episodic:
        parts.append(f"### Earlier activity with this user\n{episodic}")
        used.extend(state.get("episodic_paths") or [])

    topic = (state.get("topic_content") or "").strip()
    if topic and state.get("matched_topic_path"):
        summary, log_text = extract_topic_sections(topic)
        text = summary if summary and summary != EMPTY_SECTION else log_text
        if text:
            parts.append(f"### Notes from an earlier conversation on this question's topic\n{text}")
            used.append(state["matched_topic_path"])

    if not parts:
        return "", []
    return MEMORY_INSTRUCTIONS + "\n\n" + "\n\n".join(parts), used


@dataclass
class MemoryRead:
    block: str = ""  # text to append to the system prompt ("" = nothing)
    used: list[str] = field(default_factory=list)  # memory items injected, e.g. "user_profile.md"
    state: State = field(default_factory=dict)  # kept for write_back (matched topic etc.)
    error: str | None = None


def read_memory(user_id: str, question: str) -> MemoryRead:
    """Memory READ. `question` is the raw user question — the same text retrieval gets."""
    state: State = {"user_id": user_id, "query": question, "trace": []}
    try:
        apply(state, loading_userProfiles(state))
        # The router is an LLM call; skip it when this user has no topics yet.
        if UserMemory(user_id).load_index()["topics"]:
            apply(state, search_TopicIndex(state))
            if state.get("matched_topic_id"):
                apply(state, specific_topic(state))
        block, used = build_memory_block(state)
        return MemoryRead(block=block, used=used, state=state)
    except Exception as exc:  # a broken memory read must not kill the turn
        return MemoryRead(state=state, error=f"read_memory: {exc!r}")


def write_back(user_id: str, question: str, answer: str, read: MemoryRead) -> dict:
    """Memory WRITE, after the answer. Returns {"action", "trace", "error"}.

    Runs for refusals too (a profile statement the knowledge base cannot answer
    is exactly the kind of turn that must be remembered).
    """
    state: State = dict(read.state)  # type: ignore[assignment]
    state.update({"user_id": user_id, "query": question, "answer": answer})
    state["trace"] = list(read.state.get("trace", []))
    try:
        apply(state, decision_worth(state))
        action = state.get("memory_action", "skip")
        if action == "append":
            apply(state, append_md(state))
        elif action == "create":
            apply(state, create_md(state))
        elif action == "profile":
            apply(state, update_UserProfile(state))
        if action != "skip":
            apply(state, append_episodic(state))
        return {"action": action, "trace": state["trace"], "error": None}
    except Exception as exc:
        return {"action": state.get("memory_action"), "trace": state["trace"], "error": f"write_back: {exc!r}"}


def end_session(user_id: str, session_id: str) -> dict:
    """Session boundary: run the nightly summarisation now instead of at night."""
    try:
        return {"session_id": session_id, **consolidate(user_id, include_today=True), "error": None}
    except Exception as exc:
        return {"session_id": session_id, "error": f"end_session: {exc!r}"}


def reset_memory(user_id: str) -> None:
    """Delete everything stored for this user — leaves no state behind."""
    UserMemory(user_id).reset()

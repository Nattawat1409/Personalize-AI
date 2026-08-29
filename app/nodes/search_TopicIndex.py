from typing import Optional

from pydantic import BaseModel, Field

from app.llm import llm
from app.memory.store import find_topic, load_index, render_index_for_router
from app.models.states.state import State

ROUTER_SYSTEM_PROMPT = """You are the topic router for a personal-memory system.

You are given a list of existing topics (each with an id, category, title, and
one-line description) and a new user question. Decide whether the new question
genuinely CONTINUES one of the existing topics, OR is explicitly asking to
recall an existing topic.

Rules:
- Match if the question is really about the same subject as an existing topic
  — a merely related subject is NOT enough.
- ALSO match if the question explicitly asks to recall, review, or summarise
  a prior conversation on a subject (e.g. "what did we discuss about X",
  "remind me about X", "what do you know about X") and X clearly names one of
  the existing topics — even if the question itself contains no new
  information. This is the system's core recall behaviour; do not reject it.
- If the recall question could plausibly refer to more than one existing
  topic, pick the single closest one rather than returning null — the
  assistant can still ask a clarifying question in its answer.
- Otherwise, when genuinely in doubt, return null. Creating a slightly
  redundant new topic file is cheaper than polluting an unrelated one.
- If you match, `matched_id` MUST be exactly one of the ids shown in the list,
  copied verbatim. Never invent an id.
"""


class RouteDecision(BaseModel):
    matched_id: Optional[str] = Field(
        default=None,
        description="The id of the topic this question continues, or null if it does not belong to any existing topic.",
    )
    reason: str = Field(description="One short sentence explaining the choice.")


def search_TopicIndex(state: State) -> dict:
    index = load_index()

    if not index["topics"]:
        return {
            "matched_topic_id": None,
            "matched_topic_path": None,
            "match_reason": "index is empty",
            "topic_content": "",
            "trace": ["search_TopicIndex: index empty, no router call made"],
        }

    topic_list = render_index_for_router(index)
    prompt = (
        f"{ROUTER_SYSTEM_PROMPT}\n\nExisting topics:\n{topic_list}\n\n"
        f'New question: "{state["query"]}"'
    )

    router = llm.with_structured_output(RouteDecision)
    decision: RouteDecision = router.invoke(prompt)

    matched_id = decision.matched_id
    entry = find_topic(index, matched_id) if matched_id else None

    if matched_id and entry is None:
        # router hallucinated an id that isn't in the index — never let it
        # reach a file path, fall through to "no match"
        return {
            "matched_topic_id": None,
            "matched_topic_path": None,
            "match_reason": decision.reason,
            "topic_content": "",
            "trace": [
                f"search_TopicIndex: router returned unknown id '{matched_id}' — treating as no match"
            ],
        }

    if entry is not None:
        return {
            "matched_topic_id": matched_id,
            "matched_topic_path": entry["path"],
            "match_reason": decision.reason,
            "trace": [f"search_TopicIndex: matched '{matched_id}' — {decision.reason}"],
        }

    return {
        "matched_topic_id": None,
        "matched_topic_path": None,
        "match_reason": decision.reason,
        "topic_content": "",
        "trace": [f"search_TopicIndex: no match — {decision.reason}"],
    }

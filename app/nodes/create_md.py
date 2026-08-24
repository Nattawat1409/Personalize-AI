from app.config import CATEGORIES
from app.memory.store import create_topic
from app.models.states.state import State


def create_md(state: State) -> dict:
    category = state.get("memory_category", "general")
    if category not in CATEGORIES:
        category = "general"

    topic_id, path = create_topic(
        title=state.get("topic_title") or state["query"][:60],
        category=category,
        one_liner=state.get("topic_one_liner") or state["query"][:120],
        summary=state.get("topic_summary") or state["answer"],
        query=state["query"],
        answer=state["answer"],
    )

    return {
        "trace": [f"create_md: created '{path}' (id={topic_id}, category={category})"],
    }

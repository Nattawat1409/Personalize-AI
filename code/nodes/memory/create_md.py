"""Memory WRITE — file a new topic. Diagram box: "Create .md & Update topics_index"."""

from config.memory import CATEGORIES
from repository.memory_repository import UserMemory
from workflow.state import State


def create_md(state: State) -> dict:
    category = state.get("memory_category", "general")
    if category not in CATEGORIES:
        category = "general"

    keywords = state.get("topic_keywords") or []
    topic_id, path = UserMemory(state["user_id"]).create_topic(
        title=state.get("topic_title") or state["query"][:60],
        category=category,
        one_liner=state.get("topic_one_liner") or state["query"][:120],
        summary=state.get("topic_summary") or state["answer"],
        query=state["query"],
        answer=state["answer"],
        keywords=keywords,
    )
    return {
        "trace": [
            f"create_md: created '{path}' (id={topic_id}, category={category}, "
            f"keywords={len(keywords)})"
        ]
    }

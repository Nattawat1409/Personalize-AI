"""Memory READ, step 3 — load the one topic file the router matched."""

from repository.memory_repository import UserMemory
from workflow.state import State


def specific_topic(state: State) -> dict:
    path = state.get("matched_topic_path")
    content = UserMemory(state["user_id"]).read_topic(path) if path else ""

    if path and not content:
        return {
            "topic_content": "",
            "trace": [f"specific_topic: expected file '{path}' missing on disk, continuing without it"],
        }
    return {
        "topic_content": content,
        "trace": [f"specific_topic: read {len(content)} chars from '{path}'"],
    }

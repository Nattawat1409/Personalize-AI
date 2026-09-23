"""Memory WRITE — log the turn to today's episodic file.
Diagram box: "Append episodic/YYYY-MM-DD.md".

Runs on every turn decision_worth judged worth remembering (every action but
"skip"), in addition to whichever topic/profile write also ran — the one
deliberate departure from the v1 diagram's exclusive 4-way branch.
"""

from repository.memory_repository import UserMemory
from workflow.state import State


def append_episodic(state: State) -> dict:
    gist = (
        state.get("episodic_gist")
        or state.get("topic_summary")
        or state.get("profile_update")
        or state["answer"][:200]
    )
    category = state.get("episodic_category") or state.get("memory_category") or "general"
    path = UserMemory(state["user_id"]).append_episodic_entry(
        query=state["query"], gist=gist, category=category
    )
    return {"trace": [f"append_episodic: logged to '{path}' (category={category})"]}
